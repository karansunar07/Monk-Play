document.querySelectorAll(".flash-message").forEach((message) => {
    message.setAttribute("role", "status");
});

const audioPlayer = document.querySelector("#site-audio-player");
const playableRows = Array.from(document.querySelectorAll(".playable-track")).filter(
    (row) => row.dataset.src || row.dataset.embedUrl
);

if (audioPlayer && playableRows.length) {
    const musicPlayer = document.querySelector(".music-player");
    const titleEl = document.querySelector("#player-title");
    const artistEl = document.querySelector("#player-artist");
    const coverEl = document.querySelector("#player-cover");
    const embedWrap = document.querySelector("#player-embed-wrap");
    const spotifyEmbed = document.querySelector("#player-spotify-embed");
    const playPauseBtn = document.querySelector("#play-pause-btn");
    const closePlayerBtn = document.querySelector("#close-player-btn");
    const prevBtn = document.querySelector("#prev-btn");
    const nextBtn = document.querySelector("#next-btn");
    const shuffleBtn = document.querySelector("#shuffle-btn");
    const repeatBtn = document.querySelector("#repeat-btn");
    const muteBtn = document.querySelector("#mute-btn");
    const progressRange = document.querySelector("#progress-range");
    const volumeRange = document.querySelector("#volume-range");
    const currentTimeEl = document.querySelector("#current-time");
    const totalTimeEl = document.querySelector("#total-time");
    let currentIndex = 0;
    let isShuffle = false;
    let isRepeat = false;
    let wasMutedVolume = Number(volumeRange.value) || 0.8;

    const formatTime = (seconds) => {
        if (!Number.isFinite(seconds) || seconds < 0) {
            return "0:00";
        }

        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60).toString().padStart(2, "0");
        return `${minutes}:${remainingSeconds}`;
    };

    const setActiveRow = () => {
        playableRows.forEach((row, index) => {
            const isActive = index === currentIndex;
            row.classList.toggle("active-track", isActive);
            const button = row.querySelector(".track-play-btn");
            if (button) {
                button.textContent = isActive && (!audioPlayer.paused || row.dataset.embedUrl)
                    ? "Pause"
                    : button.dataset.playLabel || "Play";
            }
        });
    };

    const loadTrack = (index, shouldPlay = false) => {
        currentIndex = (index + playableRows.length) % playableRows.length;
        const track = playableRows[currentIndex].dataset;
        titleEl.textContent = track.title || "Untitled track";
        artistEl.textContent = track.artist || "Unknown artist";
        if (coverEl && coverEl.tagName === "IMG" && track.cover) {
            coverEl.src = track.cover;
        }
        totalTimeEl.textContent = formatTime(Number(track.duration || 0) / 1000);
        progressRange.value = 0;
        currentTimeEl.textContent = "0:00";
        musicPlayer.classList.remove("is-hidden");
        musicPlayer.classList.toggle("has-embed", Boolean(track.embedUrl));

        if (track.embedUrl) {
            audioPlayer.pause();
            audioPlayer.removeAttribute("src");
            audioPlayer.load();
            if (spotifyEmbed && spotifyEmbed.src !== track.embedUrl) {
                spotifyEmbed.src = track.embedUrl;
            }
            if (embedWrap) {
                embedWrap.hidden = false;
            }
            playPauseBtn.classList.remove("playing");
            playPauseBtn.setAttribute("aria-label", "Play in Spotify embed");
            setActiveRow();
            return;
        }

        if (embedWrap) {
            embedWrap.hidden = true;
        }
        musicPlayer.classList.remove("has-embed");
        if (spotifyEmbed) {
            spotifyEmbed.removeAttribute("src");
        }
        audioPlayer.src = track.src;
        setActiveRow();

        if (shouldPlay) {
            audioPlayer.play().catch(() => {
                playPauseBtn.classList.remove("playing");
                playPauseBtn.setAttribute("aria-label", "Play");
                setActiveRow();
            });
        }
    };

    const togglePlay = () => {
        if (!audioPlayer.src) {
            loadTrack(currentIndex, true);
            return;
        }

        if (playableRows[currentIndex].dataset.embedUrl) {
            loadTrack(currentIndex, false);
            return;
        }

        if (audioPlayer.paused) {
            audioPlayer.play();
        } else {
            audioPlayer.pause();
        }
    };

    const playNext = () => {
        const nextIndex = isShuffle
            ? Math.floor(Math.random() * playableRows.length)
            : currentIndex + 1;
        loadTrack(nextIndex, true);
    };

    const updatePlayState = () => {
        const isPlaying = !audioPlayer.paused;
        playPauseBtn.classList.toggle("playing", isPlaying);
        playPauseBtn.setAttribute("aria-label", isPlaying ? "Pause" : "Play");
        setActiveRow();
    };

    playableRows.forEach((row, index) => {
        const button = row.querySelector(".track-play-btn");
        if (!button) {
            return;
        }

        button.addEventListener("click", () => {
            if (index === currentIndex && audioPlayer.src && !row.dataset.embedUrl) {
                togglePlay();
                return;
            }

            loadTrack(index, true);
        });
    });

    playPauseBtn.addEventListener("click", togglePlay);
    if (closePlayerBtn) {
        closePlayerBtn.addEventListener("click", () => {
            audioPlayer.pause();
            musicPlayer.classList.add("is-hidden");
        });
    }
    prevBtn.addEventListener("click", () => loadTrack(currentIndex - 1, true));
    nextBtn.addEventListener("click", playNext);

    shuffleBtn.addEventListener("click", () => {
        isShuffle = !isShuffle;
        shuffleBtn.classList.toggle("active", isShuffle);
    });

    repeatBtn.addEventListener("click", () => {
        isRepeat = !isRepeat;
        repeatBtn.classList.toggle("active", isRepeat);
    });

    progressRange.addEventListener("input", () => {
        if (!Number.isFinite(audioPlayer.duration) || audioPlayer.duration <= 0) {
            return;
        }

        audioPlayer.currentTime = (Number(progressRange.value) / 100) * audioPlayer.duration;
    });

    volumeRange.addEventListener("input", () => {
        audioPlayer.volume = Number(volumeRange.value);
        audioPlayer.muted = audioPlayer.volume === 0;
        muteBtn.classList.toggle("muted", audioPlayer.muted);
    });

    muteBtn.addEventListener("click", () => {
        if (audioPlayer.muted || audioPlayer.volume === 0) {
            audioPlayer.muted = false;
            audioPlayer.volume = wasMutedVolume;
            volumeRange.value = wasMutedVolume;
        } else {
            wasMutedVolume = audioPlayer.volume || Number(volumeRange.value) || 0.8;
            audioPlayer.muted = true;
            volumeRange.value = 0;
        }

        muteBtn.classList.toggle("muted", audioPlayer.muted);
    });

    audioPlayer.addEventListener("loadedmetadata", () => {
        totalTimeEl.textContent = formatTime(audioPlayer.duration);
    });

    audioPlayer.addEventListener("timeupdate", () => {
        currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
        if (Number.isFinite(audioPlayer.duration) && audioPlayer.duration > 0) {
            progressRange.value = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        }
    });

    audioPlayer.addEventListener("play", updatePlayState);
    audioPlayer.addEventListener("pause", updatePlayState);
    audioPlayer.addEventListener("ended", () => {
        if (isRepeat) {
            loadTrack(currentIndex, true);
            return;
        }

        playNext();
    });

    audioPlayer.volume = Number(volumeRange.value);
    loadTrack(0, false);
}
