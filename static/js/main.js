const playButtons = document.querySelectorAll(".play-btn");
const togglePlayButton = document.querySelector("#toggle-play");
const playerTitle = document.querySelector("#player-title");
const playerSubtitle = document.querySelector("#player-subtitle");
const copyTargetButtons = document.querySelectorAll("[data-copy-target]");
const copyTextButtons = document.querySelectorAll("[data-copy-text]");

let isPlaying = false;

function syncPlayButton() {
    if (!togglePlayButton) {
        return;
    }

    togglePlayButton.textContent = isPlaying ? "Pause" : "Play";
}

async function copyText(value) {
    try {
        await navigator.clipboard.writeText(value);
    } catch (error) {
        console.error("Copy failed:", error);
    }
}

togglePlayButton?.addEventListener("click", () => {
    isPlaying = !isPlaying;
    syncPlayButton();
});

playButtons.forEach((button) => {
    button.addEventListener("click", () => {
        if (playerTitle) {
            playerTitle.textContent = button.dataset.playlist;
        }

        if (playerSubtitle) {
            playerSubtitle.textContent = "Playlist selected";
        }

        isPlaying = true;
        syncPlayButton();
    });
});

copyTargetButtons.forEach((button) => {
    button.addEventListener("click", async () => {
        const target = document.getElementById(button.dataset.copyTarget);
        if (!target) {
            return;
        }

        await copyText(target.value || target.textContent || "");
        const originalLabel = button.textContent;
        button.textContent = "Copied";
        window.setTimeout(() => {
            button.textContent = originalLabel;
        }, 1200);
    });
});

copyTextButtons.forEach((button) => {
    button.addEventListener("click", async () => {
        await copyText(button.dataset.copyText || "");
        button.classList.add("copied");
        window.setTimeout(() => {
            button.classList.remove("copied");
        }, 1200);
    });
});

syncPlayButton();
