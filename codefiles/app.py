import os
import json
import re
import uuid
from pathlib import Path

from flask import Flask, render_template, request, jsonify, send_from_directory
from dotenv import load_dotenv

from google import genai
from google.genai import types


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TEXT_MODEL = os.getenv(
    "TEXT_MODEL",
    "gemini-2.5-flash"
)

IMAGE_MODEL = os.getenv(
    "IMAGE_MODEL",
    "gemini-2.5-flash-image"
)

PORT = int(
    os.getenv("FLASK_PORT", "5000")
)


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

GENERATED_DIR = BASE_DIR / "generated"

GENERATED_DIR.mkdir(
    exist_ok=True
)


# ============================================================
# GEMINI CLIENT
# ============================================================

client = None

if GEMINI_API_KEY:

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health")
def health():

    return jsonify({
        "status": "ok",
        "application": "ComicCraft",
        "gemini_configured": bool(GEMINI_API_KEY),
        "text_model": TEXT_MODEL,
        "image_model": IMAGE_MODEL
    })


# ============================================================
# CLEAN GEMINI JSON RESPONSE
# ============================================================

def clean_json_response(text):

    if not text:
        raise ValueError(
            "Gemini returned an empty response."
        )

    text = text.strip()

    # Remove markdown code fences

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


# ============================================================
# GENERATE STORY
# ============================================================

def generate_story(
    idea,
    genre,
    panel_count,
    art_style,
    characters,
    tone
):

    if client is None:

        raise RuntimeError(
            "Gemini API key is not configured."
        )


    character_text = characters.strip()

    if not character_text:

        character_text = (
            "Create suitable original characters "
            "based on the user's idea."
        )


    prompt = f"""
You are ComicCraft, an expert AI comic-book
writer and storyboard designer.

Create an original comic story.

USER IDEA:
{idea}

GENRE:
{genre}

NUMBER OF PANELS:
{panel_count}

ART STYLE:
{art_style}

CHARACTERS:
{character_text}

STORY TONE:
{tone}


IMPORTANT REQUIREMENTS:

1. Create an original comic title.

2. Create a short story summary.

3. Create a list of important characters.

4. Create exactly {panel_count} panels.

5. Every panel must contain:

   - panelNumber
   - scene
   - visualDescription
   - dialogue
   - caption

6. Maintain character consistency.

7. Make the story suitable for a college
   Generative AI project demonstration.

8. Make each panel visually clear.

9. Do not use markdown.

10. Return ONLY valid JSON.

Use exactly this JSON structure:

{{
    "title": "Comic title",

    "genre": "{genre}",

    "storySummary": "Short story summary",

    "characters": [
        {{
            "name": "Character name",
            "description": "Character appearance and personality"
        }}
    ],

    "panels": [
        {{
            "panelNumber": 1,

            "scene": "Scene name",

            "visualDescription":
                "Detailed visual description",

            "dialogue": [
                {{
                    "speaker": "Character",
                    "text": "Dialogue"
                }}
            ],

            "caption":
                "Narration caption"
        }}
    ]
}}
"""


    response = client.models.generate_content(

        model=TEXT_MODEL,

        contents=prompt,

        config=types.GenerateContentConfig(
            temperature=0.8
        )
    )


    response_text = response.text

    cleaned = clean_json_response(
        response_text
    )


    try:

        story = json.loads(
            cleaned
        )

    except json.JSONDecodeError as error:

        print(
            "Invalid JSON returned by Gemini:"
        )

        print(cleaned)

        raise ValueError(
            "Gemini returned an invalid story format."
        ) from error


    if "panels" not in story:

        raise ValueError(
            "Gemini did not generate comic panels."
        )


    if not isinstance(
        story["panels"],
        list
    ):

        raise ValueError(
            "Comic panels have an invalid format."
        )


    # Make sure we don't exceed requested number

    story["panels"] = story["panels"][
        :panel_count
    ]


    return story


# ============================================================
# GENERATE IMAGE FOR ONE PANEL
# ============================================================

def generate_panel_image(
    comic_title,
    art_style,
    characters,
    panel,
    panel_number,
    total_panels
):

    if client is None:

        raise RuntimeError(
            "Gemini API key is not configured."
        )


    character_description = "\n".join(

        [
            f"{character.get('name', 'Character')}: "
            f"{character.get('description', '')}"

            for character in characters
        ]

    )


    dialogue_text = "\n".join(

        [
            f"{item.get('speaker', 'Character')}: "
            f"{item.get('text', '')}"

            for item in panel.get(
                "dialogue",
                []
            )
        ]

    )


    prompt = f"""
Create ONE professional comic-book panel.

COMIC TITLE:
{comic_title}

PANEL:
{panel_number} of {total_panels}

ART STYLE:
{art_style}

CHARACTER DESCRIPTIONS:
{character_description}

SCENE:
{panel.get('scene', '')}

VISUAL DESCRIPTION:
{panel.get('visualDescription', '')}

DIALOGUE:
{dialogue_text}

CAPTION:
{panel.get('caption', '')}


VISUAL REQUIREMENTS:

- Create exactly ONE comic panel.
- Use a professional comic-book composition.
- Keep character appearance consistent.
- Use expressive facial expressions.
- Use cinematic lighting.
- Make the scene easy to understand.
- Use speech bubbles when appropriate.
- Do NOT create multiple panels.
- Do NOT create a full comic page.
- Do NOT add panel numbers.
- Do NOT add a title outside the artwork.
- Avoid random unreadable text.
- Focus mainly on characters and visual storytelling.
"""


    response = client.models.generate_content(

        model=IMAGE_MODEL,

        contents=prompt,

        config=types.GenerateContentConfig(

            response_modalities=[
                "IMAGE"
            ],

            response_format={
                "image": {
                    "aspect_ratio": "4:3"
                }
            }
        )
    )


    image_data = None


    # Search response parts for generated image

    try:

        for part in response.parts:

            if getattr(
                part,
                "inline_data",
                None
            ):

                image_data = (
                    part.inline_data.data
                )

                break

    except Exception:

        pass


    if image_data is None:

        raise RuntimeError(
            f"Image generation failed "
            f"for panel {panel_number}."
        )


    # Create unique filename

    filename = (
        f"comic_{uuid.uuid4().hex}.png"
    )


    filepath = (
        GENERATED_DIR / filename
    )


    # Save image

    if isinstance(
        image_data,
        bytes
    ):

        image_bytes = image_data

    else:

        import base64

        image_bytes = base64.b64decode(
            image_data
        )


    with open(
        filepath,
        "wb"
    ) as file:

        file.write(
            image_bytes
        )


    return filename


# ============================================================
# GENERATE COMPLETE COMIC
# ============================================================

@app.route(
    "/api/generate-comic",
    methods=["POST"]
)
def generate_comic():

    try:

        # ----------------------------------------------------
        # CHECK API KEY
        # ----------------------------------------------------

        if not GEMINI_API_KEY:

            return jsonify({

                "success": False,

                "error":
                    "Gemini API key is missing. "
                    "Please add GEMINI_API_KEY "
                    "to the .env file."

            }), 500


        # ----------------------------------------------------
        # GET REQUEST DATA
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        )


        if not data:

            return jsonify({

                "success": False,

                "error":
                    "No data was received."

            }), 400


        idea = str(
            data.get(
                "idea",
                ""
            )
        ).strip()


        genre = str(
            data.get(
                "genre",
                "Adventure"
            )
        )


        panel_count = int(
            data.get(
                "panelCount",
                4
            )
        )


        art_style = str(
            data.get(
                "artStyle",
                "Modern Comic Book"
            )
        )


        characters = str(
            data.get(
                "characters",
                ""
            )
        )


        tone = str(
            data.get(
                "tone",
                "Fun and Lighthearted"
            )
        )


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if len(idea) < 5:

            return jsonify({

                "success": False,

                "error":
                    "Please enter a comic idea "
                    "with at least 5 characters."

            }), 400


        # Limit panels

        panel_count = max(
            1,
            min(
                panel_count,
                8
            )
        )


        # ----------------------------------------------------
        # GENERATE STORY
        # ----------------------------------------------------

        print(
            "\nGenerating comic story..."
        )


        story = generate_story(

            idea=idea,

            genre=genre,

            panel_count=panel_count,

            art_style=art_style,

            characters=characters,

            tone=tone
        )


        # ----------------------------------------------------
        # GENERATE IMAGES
        # ----------------------------------------------------

        generated_panels = []


        total_panels = len(
            story["panels"]
        )


        for index, panel in enumerate(

            story["panels"],

            start=1

        ):

            print(
                f"Generating image "
                f"{index}/{total_panels}..."
            )


            try:

                filename = generate_panel_image(

                    comic_title=story.get(
                        "title",
                        "ComicCraft"
                    ),

                    art_style=art_style,

                    characters=story.get(
                        "characters",
                        []
                    ),

                    panel=panel,

                    panel_number=index,

                    total_panels=total_panels
                )


                panel["panelNumber"] = index

                panel["imageUrl"] = (
                    f"/generated/{filename}"
                )

                panel["imageError"] = None


            except Exception as image_error:

                print(
                    f"Image error for "
                    f"panel {index}: "
                    f"{image_error}"
                )


                panel["panelNumber"] = index

                panel["imageUrl"] = None

                panel["imageError"] = (
                    str(image_error)
                )


            generated_panels.append(
                panel
            )


        story["panels"] = (
            generated_panels
        )


        # ----------------------------------------------------
        # RETURN RESULT
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "comic": story

        })


    except Exception as error:

        print(
            "\nComic generation error:"
        )

        print(error)


        return jsonify({

            "success": False,

            "error": str(error)

        }), 500


# ============================================================
# SERVE GENERATED IMAGES
# ============================================================

@app.route(
    "/generated/<path:filename>"
)
def generated_file(filename):

    return send_from_directory(

        GENERATED_DIR,

        filename
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 50)
    print("           COMICCRAFT AI")
    print("=" * 50)
    print(
        f"Server running at:"
        f" http://localhost:{PORT}"
    )
    print("=" * 50)
    print()


    app.run(

        host="127.0.0.1",

        port=PORT,

        debug=True
    )