document.querySelectorAll(".flash-message").forEach((message) => {
    message.setAttribute("role", "status");
});

const globalSearchForm = document.querySelector(".playbar-search");
const globalSearchInput = document.querySelector("#global-song-search");
const trackTable = document.querySelector(".track-table");
const trackRows = Array.from(document.querySelectorAll(".track-table .playable-track"));
const isSongsPage = window.location.pathname.replace(/\/$/, "") === "/songs";

if (globalSearchForm && globalSearchInput && !isSongsPage) {
    globalSearchForm.addEventListener("submit", () => {
        globalSearchInput.value = globalSearchInput.value.trim();
    });
}

if (globalSearchForm && globalSearchInput && trackTable && trackRows.length && isSongsPage) {
    const noResultsRow = document.createElement("div");
    noResultsRow.className = "track-row search-empty-row";
    noResultsRow.style.display = "none";
    noResultsRow.innerHTML = `
        <div class="track-main">
            <span class="track-number">0</span>
            <div>
                <h3>No matching songs</h3>
                <p>Try another title, artist, album, or playlist name.</p>
            </div>
        </div>
        <span class="track-tag">Search</span>
        <span class="track-time">0:00</span>
    `;
    trackTable.appendChild(noResultsRow);

    const filterSongs = () => {
        const query = globalSearchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        trackRows.forEach((row) => {
            const values = [
                row.dataset.title,
                row.dataset.artist,
                row.dataset.album,
                row.dataset.playlist,
                row.textContent,
            ].join(" ").toLowerCase();
            const isVisible = !query || values.includes(query);
            row.style.display = isVisible ? "" : "none";

            if (isVisible) {
                visibleCount += 1;
                const numberEl = row.querySelector(".track-number");
                if (numberEl) {
                    numberEl.textContent = String(visibleCount);
                }
            }
        });

        noResultsRow.style.display = visibleCount > 0 ? "none" : "";
    };

    globalSearchForm.addEventListener("submit", (event) => {
        event.preventDefault();
        filterSongs();
    });
    globalSearchInput.addEventListener("input", filterSongs);
    filterSongs();
}

const audioPlayer = document.querySelector("#site-audio-player");
const playableRows = Array.from(document.querySelectorAll(".playable-track")).filter(
    (row) => row.dataset.src || row.dataset.embedUrl
);
const PLAYER_STATE_KEY = "monkPlayerState";

const readStoredPlayerState = () => {
    try {
        return JSON.parse(sessionStorage.getItem(PLAYER_STATE_KEY) || "null");
    } catch (_error) {
        return null;
    }
};

const storedPlayerStateAtLoad = readStoredPlayerState();

if (audioPlayer && (playableRows.length || storedPlayerStateAtLoad)) {
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
    let spotifyAutoNextTimer = null;
    let standaloneTrackState = null;
    let wasMutedVolume = Number(localStorage.getItem("monkPlayerVolume")) || Number(volumeRange.value) || 0.8;

    const getTrackKey = (track) => track.src || track.embedUrl || `${track.title || ""}|${track.artist || ""}`;

    const getStoredPlayerState = () => readStoredPlayerState();

    const getCurrentTrackData = () => playableRows[currentIndex]?.dataset || standaloneTrackState;

    const rememberPlayerState = () => {
        const track = getCurrentTrackData();
        if (!track) {
            return;
        }

        const isSpotifyTrack = Boolean(track.embedUrl);
        sessionStorage.setItem(
            PLAYER_STATE_KEY,
            JSON.stringify({
                key: getTrackKey(track),
                currentTime: isSpotifyTrack ? 0 : audioPlayer.currentTime || 0,
                wasPlaying: isSpotifyTrack ? playPauseBtn.classList.contains("playing") : !audioPlayer.paused,
                isSpotifyTrack,
                title: track.title || "",
                artist: track.artist || "",
                cover: track.cover || "",
                duration: track.duration || "0",
                src: track.src || "",
                embedUrl: track.embedUrl || "",
            }),
        );
    };

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
                if (row.dataset.embedUrl) {
                    button.textContent = isActive ? "Playing" : button.dataset.playLabel || "Play";
                    return;
                }

                button.textContent = isActive && !audioPlayer.paused
                    ? "Pause"
                    : button.dataset.playLabel || "Play";
            }
        });
    };

    const clearSpotifyAutoNext = () => {
        if (spotifyAutoNextTimer) {
            window.clearTimeout(spotifyAutoNextTimer);
            spotifyAutoNextTimer = null;
        }
    };

    const scheduleSpotifyAutoNext = (track) => {
        clearSpotifyAutoNext();
        const duration = Number(track.duration || 0);
        if (!Number.isFinite(duration) || duration <= 0) {
            return;
        }

        spotifyAutoNextTimer = window.setTimeout(() => {
            if (isRepeat) {
                loadTrack(currentIndex, true);
                return;
            }

            playNext();
        }, duration + 1200);
    };

    const loadTrack = (index, shouldPlay = false) => {
        if (!playableRows.length) {
            return;
        }

        clearSpotifyAutoNext();
        currentIndex = (index + playableRows.length) % playableRows.length;
        standaloneTrackState = null;
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
            volumeRange.disabled = true;
            muteBtn.disabled = true;
            muteBtn.setAttribute("aria-label", "Spotify embed volume is controlled inside Spotify");
            if (spotifyEmbed && spotifyEmbed.src !== track.embedUrl) {
                spotifyEmbed.src = track.embedUrl;
            }
            if (embedWrap) {
                embedWrap.hidden = false;
            }
            playPauseBtn.classList.remove("playing");
            playPauseBtn.classList.toggle("playing", shouldPlay);
            playPauseBtn.setAttribute("aria-label", shouldPlay ? "Spotify track selected" : "Play");
            setActiveRow();
            if (shouldPlay) {
                scheduleSpotifyAutoNext(track);
            }
            return;
        }

        if (embedWrap) {
            embedWrap.hidden = true;
        }
        musicPlayer.classList.remove("has-embed");
        volumeRange.disabled = false;
        muteBtn.disabled = false;
        muteBtn.setAttribute("aria-label", audioPlayer.muted ? "Unmute" : "Mute");
        if (spotifyEmbed) {
            spotifyEmbed.removeAttribute("src");
        }
        audioPlayer.src = track.src;
        audioPlayer.volume = Number(volumeRange.value);
        setActiveRow();
        rememberPlayerState();

        if (shouldPlay) {
            audioPlayer.play().catch(() => {
                playPauseBtn.classList.remove("playing");
                playPauseBtn.setAttribute("aria-label", "Play");
                setActiveRow();
            });
        }
    };

    const restoreStoredTrackOnly = (storedState) => {
        if (!storedState?.src && !storedState?.embedUrl) {
            return false;
        }

        clearSpotifyAutoNext();
        standaloneTrackState = {
            title: storedState.title || "",
            artist: storedState.artist || "",
            cover: storedState.cover || "",
            duration: storedState.duration || "0",
            src: storedState.src || "",
            embedUrl: storedState.embedUrl || "",
        };
        titleEl.textContent = storedState.title || "Untitled track";
        artistEl.textContent = storedState.artist || "Unknown artist";
        totalTimeEl.textContent = formatTime(Number(storedState.duration || 0) / 1000);
        progressRange.value = 0;
        currentTimeEl.textContent = "0:00";
        musicPlayer.classList.remove("is-hidden");
        playableRows.forEach((row) => row.classList.remove("active-track"));

        if (coverEl && coverEl.tagName === "IMG" && storedState.cover) {
            coverEl.src = storedState.cover;
        }

        if (storedState.embedUrl) {
            audioPlayer.pause();
            audioPlayer.removeAttribute("src");
            audioPlayer.load();
            musicPlayer.classList.add("has-embed");
            volumeRange.disabled = true;
            muteBtn.disabled = true;
            if (spotifyEmbed) {
                spotifyEmbed.src = storedState.embedUrl;
            }
            if (embedWrap) {
                embedWrap.hidden = false;
            }
            playPauseBtn.classList.toggle("playing", Boolean(storedState.wasPlaying));
            playPauseBtn.setAttribute("aria-label", storedState.wasPlaying ? "Spotify track selected" : "Play");
            if (storedState.wasPlaying) {
                scheduleSpotifyAutoNext({
                    duration: storedState.duration,
                    embedUrl: storedState.embedUrl,
                });
            }
            return true;
        }

        if (embedWrap) {
            embedWrap.hidden = true;
        }
        if (spotifyEmbed) {
            spotifyEmbed.removeAttribute("src");
        }
        musicPlayer.classList.remove("has-embed");
        volumeRange.disabled = false;
        muteBtn.disabled = false;
        audioPlayer.src = storedState.src;
        audioPlayer.volume = Number(volumeRange.value);

        const restoreLocalPlayback = () => {
            const restoreTime = Number(storedState.currentTime || 0);
            if (Number.isFinite(restoreTime) && restoreTime > 0 && restoreTime < audioPlayer.duration) {
                audioPlayer.currentTime = restoreTime;
            }
            if (storedState.wasPlaying) {
                audioPlayer.play().catch(() => updatePlayState());
            }
            updatePlayState();
        };

        if (audioPlayer.readyState >= 1) {
            restoreLocalPlayback();
        } else {
            audioPlayer.addEventListener("loadedmetadata", restoreLocalPlayback, { once: true });
        }
        return true;
    };

    const togglePlay = () => {
        const currentTrack = getCurrentTrackData();
        if (!audioPlayer.src && !currentTrack?.embedUrl) {
            if (playableRows.length) {
                loadTrack(currentIndex, true);
            }
            return;
        }

        if (currentTrack?.embedUrl) {
            if (embedWrap) {
                embedWrap.hidden = false;
            }
            playPauseBtn.classList.add("playing");
            playPauseBtn.setAttribute("aria-label", "Spotify track selected");
            scheduleSpotifyAutoNext(currentTrack);
            setActiveRow();
            rememberPlayerState();
            return;
        }

        if (!audioPlayer.src) {
            loadTrack(currentIndex, true);
            return;
        }

        if (audioPlayer.paused) {
            audioPlayer.play();
        } else {
            audioPlayer.pause();
        }
    };

    const getVisiblePlayableRows = () => {
        const visibleRows = playableRows.filter((row) => row.style.display !== "none");
        return visibleRows.length ? visibleRows : playableRows;
    };

    const getAdjacentTrackIndex = (direction) => {
        const queue = getVisiblePlayableRows();
        if (!queue.length) {
            return currentIndex;
        }

        if (isShuffle) {
            return playableRows.indexOf(queue[Math.floor(Math.random() * queue.length)]);
        }

        const queueIndex = queue.indexOf(playableRows[currentIndex]);
        if (queueIndex === -1) {
            return (currentIndex + direction + playableRows.length) % playableRows.length;
        }

        const nextQueueIndex = (queueIndex + direction + queue.length) % queue.length;
        return playableRows.indexOf(queue[nextQueueIndex]);
    };

    const playNext = () => {
        if (!playableRows.length) {
            return;
        }

        loadTrack(getAdjacentTrackIndex(1), true);
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
            clearSpotifyAutoNext();
            audioPlayer.pause();
            musicPlayer.classList.add("is-hidden");
            sessionStorage.removeItem(PLAYER_STATE_KEY);
        });
    }
    prevBtn.addEventListener("click", () => {
        if (playableRows.length) {
            loadTrack(getAdjacentTrackIndex(-1), true);
        }
    });
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

    const applyVolume = () => {
        const nextVolume = Number(volumeRange.value);
        audioPlayer.volume = nextVolume;
        audioPlayer.muted = audioPlayer.volume === 0;
        if (nextVolume > 0) {
            wasMutedVolume = nextVolume;
        }
        localStorage.setItem("monkPlayerVolume", String(nextVolume));
        muteBtn.classList.toggle("muted", audioPlayer.muted);
        muteBtn.setAttribute("aria-label", audioPlayer.muted ? "Unmute" : "Mute");
    };

    volumeRange.addEventListener("input", applyVolume);
    volumeRange.addEventListener("change", applyVolume);

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
        muteBtn.setAttribute("aria-label", audioPlayer.muted ? "Unmute" : "Mute");
        localStorage.setItem("monkPlayerVolume", String(Number(volumeRange.value)));
    });

    audioPlayer.addEventListener("loadedmetadata", () => {
        totalTimeEl.textContent = formatTime(audioPlayer.duration);
    });

    audioPlayer.addEventListener("timeupdate", () => {
        currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
        if (Number.isFinite(audioPlayer.duration) && audioPlayer.duration > 0) {
            progressRange.value = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        }
        rememberPlayerState();
    });

    audioPlayer.addEventListener("play", updatePlayState);
    audioPlayer.addEventListener("play", rememberPlayerState);
    audioPlayer.addEventListener("pause", updatePlayState);
    audioPlayer.addEventListener("pause", rememberPlayerState);
    audioPlayer.addEventListener("ended", () => {
        if (isRepeat) {
            loadTrack(currentIndex, true);
            return;
        }

        playNext();
    });

    volumeRange.value = wasMutedVolume;
    audioPlayer.volume = wasMutedVolume;
    const storedPlayerState = getStoredPlayerState();
    const storedTrackIndex = storedPlayerState && playableRows.length
        ? playableRows.findIndex((row) => getTrackKey(row.dataset) === storedPlayerState.key)
        : -1;

    const restoredWithoutRow = storedPlayerState
        && (storedTrackIndex === -1 || !playableRows.length)
        && restoreStoredTrackOnly(storedPlayerState);

    if (!restoredWithoutRow && playableRows.length) {
        loadTrack(storedTrackIndex >= 0 ? storedTrackIndex : 0, false);
        if (storedPlayerState && storedTrackIndex >= 0 && !playableRows[storedTrackIndex].dataset.embedUrl) {
            const restoreLocalPlayback = () => {
                const restoreTime = Number(storedPlayerState.currentTime || 0);
                if (Number.isFinite(restoreTime) && restoreTime > 0 && restoreTime < audioPlayer.duration) {
                    audioPlayer.currentTime = restoreTime;
                }
                if (storedPlayerState.wasPlaying) {
                    audioPlayer.play().catch(() => updatePlayState());
                }
            };

            if (audioPlayer.readyState >= 1) {
                restoreLocalPlayback();
            } else {
                audioPlayer.addEventListener("loadedmetadata", restoreLocalPlayback, { once: true });
            }
        } else if (storedPlayerState?.wasPlaying && storedTrackIndex >= 0 && playableRows[storedTrackIndex].dataset.embedUrl) {
            playPauseBtn.classList.add("playing");
            scheduleSpotifyAutoNext(playableRows[storedTrackIndex].dataset);
            setActiveRow();
        }
    }
}
