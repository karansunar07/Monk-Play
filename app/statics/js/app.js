const togglePlayButton = document.querySelector("#toggle-play");
const playerTitle = document.querySelector("#player-title");
const playerSubtitle = document.querySelector("#player-subtitle");
const playlistCards = document.querySelectorAll(".playlist-card");
const volumeDownButton = document.querySelector("#volume-down");
const volumeUpButton = document.querySelector("#volume-up");
const volumeSlider = document.querySelector("#volume-slider");
const volumeValue = document.querySelector("#volume-value");

let isPlaying = false;
let currentVolume = Number(volumeSlider?.value || 70);

function syncPlayerButton() {
    if (!togglePlayButton) {
        return;
    }

    togglePlayButton.textContent = isPlaying ? "Pause" : "Play";
}

function syncVolumeControls() {
    if (volumeSlider) {
        volumeSlider.value = String(currentVolume);
        volumeSlider.style.setProperty("--volume-fill", `${currentVolume}%`);
    }

    if (volumeValue) {
        volumeValue.textContent = `${currentVolume}%`;
    }

    if (volumeDownButton) {
        volumeDownButton.disabled = currentVolume === 0;
    }

    if (volumeUpButton) {
        volumeUpButton.disabled = currentVolume === 100;
    }
}

togglePlayButton?.addEventListener("click", () => {
    isPlaying = !isPlaying;
    syncPlayerButton();
});

volumeSlider?.addEventListener("input", (event) => {
    currentVolume = Number(event.target.value);
    syncVolumeControls();
});

volumeDownButton?.addEventListener("click", () => {
    currentVolume = Math.max(0, currentVolume - 5);
    syncVolumeControls();
});

volumeUpButton?.addEventListener("click", () => {
    currentVolume = Math.min(100, currentVolume + 5);
    syncVolumeControls();
});

playlistCards.forEach((card) => {
    card.addEventListener("click", () => {
        const title = card.querySelector("h3")?.textContent;
        const subtitle = card.querySelector("p")?.textContent;

        if (playerTitle && title) {
            playerTitle.textContent = title;
        }

        if (playerSubtitle && subtitle) {
            playerSubtitle.textContent = subtitle;
        }

        isPlaying = true;
        syncPlayerButton();
    });
});

syncPlayerButton();
syncVolumeControls();
