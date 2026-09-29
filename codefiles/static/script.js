// ============================================================
// COMICCRAFT FRONTEND
// ============================================================


// Get HTML elements

const comicForm =
    document.getElementById("comicForm");

const generateButton =
    document.getElementById("generateButton");

const loading =
    document.getElementById("loading");

const loadingText =
    document.getElementById("loadingText");

const errorBox =
    document.getElementById("errorBox");

const resultSection =
    document.getElementById("resultSection");

const comicTitle =
    document.getElementById("comicTitle");

const storySummary =
    document.getElementById("storySummary");

const charactersContainer =
    document.getElementById(
        "charactersContainer"
    );

const comicPanels =
    document.getElementById(
        "comicPanels"
    );

const newComicButton =
    document.getElementById(
        "newComicButton"
    );


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHTML(value) {

    if (value === null ||
        value === undefined) {

        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ============================================================
// SHOW ERROR
// ============================================================

function showError(message) {

    errorBox.textContent =
        message;

    errorBox.classList.remove(
        "hidden"
    );
}


// ============================================================
// HIDE ERROR
// ============================================================

function hideError() {

    errorBox.textContent = "";

    errorBox.classList.add(
        "hidden"
    );
}


// ============================================================
// LOADING
// ============================================================

function showLoading() {

    loading.classList.remove(
        "hidden"
    );

    generateButton.disabled =
        true;


    document
        .getElementById("step1")
        .classList.add("active");

    document
        .getElementById("step2")
        .classList.remove("active");

    document
        .getElementById("step3")
        .classList.remove("active");


    loadingText.textContent =
        "Writing your story with Gemini";


    setTimeout(() => {

        document
            .getElementById("step2")
            .classList.add("active");

        loadingText.textContent =
            "Creating comic scenes...";

    }, 2500);


    setTimeout(() => {

        document
            .getElementById("step3")
            .classList.add("active");

        loadingText.textContent =
            "Generating comic artwork...";

    }, 5000);
}


// ============================================================
// HIDE LOADING
// ============================================================

function hideLoading() {

    loading.classList.add(
        "hidden"
    );

    generateButton.disabled =
        false;
}


// ============================================================
// RENDER CHARACTERS
// ============================================================

function renderCharacters(
    characters
) {

    charactersContainer.innerHTML =
        "";


    if (!characters ||
        characters.length === 0) {

        return;
    }


    characters.forEach(
        character => {

            const card =
                document.createElement(
                    "div"
                );

            card.className =
                "character-card";


            card.innerHTML = `

                <h4>
                    ${escapeHTML(
                        character.name
                    )}
                </h4>

                <p>
                    ${escapeHTML(
                        character.description
                    )}
                </p>

            `;


            charactersContainer
                .appendChild(card);

        }
    );
}


// ============================================================
// RENDER DIALOGUE
// ============================================================

function renderDialogue(
    dialogue
) {

    if (!dialogue ||
        dialogue.length === 0) {

        return "";
    }


    let html =
        '<div class="dialogue">';


    dialogue.forEach(
        item => {

            html += `

                <p>

                    <strong>
                        ${escapeHTML(
                            item.speaker
                        )}:
                    </strong>

                    ${escapeHTML(
                        item.text
                    )}

                </p>

            `;

        }
    );


    html +=
        "</div>";


    return html;
}


// ============================================================
// RENDER PANELS
// ============================================================

function renderPanels(
    panels
) {

    comicPanels.innerHTML =
        "";


    panels.forEach(
        panel => {

            const card =
                document.createElement(
                    "article"
                );

            card.className =
                "comic-panel";


            let imageHTML;


            if (panel.imageUrl) {

                imageHTML = `

                    <img
                        src="${escapeHTML(
                            panel.imageUrl
                        )}"
                        class="panel-image"
                        alt="Comic Panel ${panel.panelNumber}"
                    >

                `;

            } else {

                imageHTML = `

                    <div
                        class="panel-image-placeholder"
                    >

                        <div>

                            <strong>
                                Artwork unavailable
                            </strong>

                            <p>
                                ${escapeHTML(
                                    panel.imageError ||
                                    "Image generation failed."
                                )}
                            </p>

                        </div>

                    </div>

                `;
            }


            const dialogueHTML =
                renderDialogue(
                    panel.dialogue
                );


            const captionHTML =
                panel.caption
                    ? `

                        <div class="caption">

                            <strong>
                                Caption:
                            </strong>

                            ${escapeHTML(
                                panel.caption
                            )}

                        </div>

                    `
                    : "";


            const downloadHTML =
                panel.imageUrl
                    ? `

                        <button
                            class="download-button"
                            onclick="downloadImage(
                                '${escapeHTML(
                                    panel.imageUrl
                                )}',
                                'comic-panel-${panel.panelNumber}.png'
                            )"
                        >

                            ⬇ Download Panel

                        </button>

                    `
                    : "";


            card.innerHTML = `

                ${imageHTML}

                <div class="panel-content">

                    <div class="panel-number">

                        Panel ${escapeHTML(
                            panel.panelNumber
                        )}

                    </div>


                    <h3>

                        ${escapeHTML(
                            panel.scene
                        )}

                    </h3>


                    <p class="panel-scene">

                        ${escapeHTML(
                            panel.visualDescription
                        )}

                    </p>


                    ${dialogueHTML}


                    ${captionHTML}


                    ${downloadHTML}

                </div>

            `;


            comicPanels
                .appendChild(card);

        }
    );
}


// ============================================================
// DOWNLOAD IMAGE
// ============================================================

async function downloadImage(
    url,
    filename
) {

    try {

        const response =
            await fetch(url);


        const blob =
            await response.blob();


        const objectURL =
            URL.createObjectURL(
                blob
            );


        const link =
            document.createElement(
                "a"
            );


        link.href =
            objectURL;

        link.download =
            filename;


        document
            .body
            .appendChild(link);


        link.click();


        link.remove();


        URL.revokeObjectURL(
            objectURL
        );


    } catch (error) {

        alert(
            "Could not download the image."
        );

    }
}


// ============================================================
// FORM SUBMISSION
// ============================================================

comicForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();


        hideError();


        const idea =
            document
                .getElementById("idea")
                .value
                .trim();


        const genre =
            document
                .getElementById("genre")
                .value;


        const panelCount =
            Number(
                document
                    .getElementById(
                        "panelCount"
                    )
                    .value
            );


        const artStyle =
            document
                .getElementById(
                    "artStyle"
                )
                .value;


        const tone =
            document
                .getElementById(
                    "tone"
                )
                .value;


        const characters =
            document
                .getElementById(
                    "characters"
                )
                .value
                .trim();


        // Validate idea

        if (idea.length < 5) {

            showError(
                "Please enter a comic idea with at least 5 characters."
            );

            return;
        }


        // Start loading

        showLoading();


        // Hide previous result

        resultSection.classList.add(
            "hidden"
        );


        try {

            const response =
                await fetch(
                    "/api/generate-comic",
                    {

                        method:
                            "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body:
                            JSON.stringify({

                                idea:
                                    idea,

                                genre:
                                    genre,

                                panelCount:
                                    panelCount,

                                artStyle:
                                    artStyle,

                                characters:
                                    characters,

                                tone:
                                    tone

                            })

                    }
                );


            const data =
                await response.json();


            if (!response.ok ||
                !data.success) {

                throw new Error(
                    data.error ||
                    "Comic generation failed."
                );
            }


            const comic =
                data.comic;


            // Display title

            comicTitle.textContent =
                comic.title ||
                "My AI Comic";


            // Display summary

            storySummary.textContent =
                comic.storySummary ||
                "";


            // Display characters

            renderCharacters(
                comic.characters || []
            );


            // Display panels

            renderPanels(
                comic.panels || []
            );


            // Show result

            resultSection.classList.remove(
                "hidden"
            );


            // Scroll to result

            setTimeout(() => {

                resultSection.scrollIntoView({

                    behavior:
                        "smooth",

                    block:
                        "start"

                });

            }, 100);


        } catch (error) {

            console.error(
                error
            );


            showError(
                error.message ||
                "Something went wrong."
            );


        } finally {

            hideLoading();

        }

    }
);


// ============================================================
// CREATE NEW COMIC
// ============================================================

newComicButton.addEventListener(
    "click",
    function() {

        resultSection.classList.add(
            "hidden"
        );


        comicForm.reset();


        window.scrollTo({

            top:
                0,

            behavior:
                "smooth"

        });

    }
);