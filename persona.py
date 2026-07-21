import random
from dataclasses import dataclass

import discord

from config import PERSONA_ENABLED


@dataclass(frozen=True)
class PersonaPool:
    """A pool of persona templates for a single event."""

    templates: tuple[str, ...]
    description: str = ""
    required_keys: tuple[str, ...] = ()


class PersonaEvents:
    """Registry of all named persona events. Use these constants instead of raw strings."""

    # ── STATUS ───────────────────────────────────────────────────────────────
    STATUS_IDLE = "status_idle"
    STATUS_PLAYING = "status_playing"

    # ── PLAYBACK LIFECYCLE ──────────────────────────────────────────────────
    SONG_STARTED = "song_started"
    SONG_FINISHED = "song_finished"
    NOW_PLAYING = "now_playing"
    NOW_PLAYING_TITLE = "now_playing_title"
    NOW_PLAYING_FOOTER = "now_playing_footer"
    QUEUED = "queued"
    QUEUED_TITLE = "queued_title"
    QUEUED_FOOTER = "queued_footer"
    QUEUED_MULTIPLE = "queued_multiple"
    PLAYNEXT = "playnext"
    PLAYNEXT_MULTIPLE = "playnext_multiple"
    PLAYLIST_LOADED = "playlist_loaded"
    SEARCHING = "searching"
    SEARCH_RESULTS = "search_results"

    # ── QUEUE CONTROL ────────────────────────────────────────────────────────
    SKIPPED = "skipped"
    SKIPTO = "skipto"
    SHUFFLE = "shuffle"
    REMOVED = "removed"
    CLEARED = "cleared"
    LOOP_ONE = "loop_one"
    LOOP_QUEUE = "loop_queue"
    LOOP_OFF = "loop_off"
    QUEUE_EMPTY = "queue_empty"
    QUEUE_SHOWING = "queue_showing"
    QUEUE_FOOTER = "queue_footer"

    # ── BOT MOVEMENT ─────────────────────────────────────────────────────────
    JOINED_VC = "joined_vc"
    LEFT_VC = "left_vc"
    MOVED_VC = "moved_vc"
    DISCONNECT_EMPTY = "disconnect_empty"

    # ── ERRORS ───────────────────────────────────────────────────────────────
    NOTHING_PLAYING = "nothing_playing"
    NOT_PAUSED = "not_paused"
    ALREADY_PLAYING = "already_playing"
    INVALID_POSITION = "invalid_position"
    NO_VOICE_CHANNEL = "no_voice_channel"
    WRONG_VOICE_CHANNEL = "wrong_voice_channel"
    OFFLINE = "offline"
    NO_RESULTS = "no_results"
    YT_DLP_ERROR = "yt_dlp_error"
    GENERIC_ERROR = "generic_error"

    # ── UTILITY ──────────────────────────────────────────────────────────────
    HELP = "help"
    HELP_TITLE = "help_title"
    HELP_FOOTER = "help_footer"
    RETRY = "retry"
    PAUSED = "paused"
    RESUMED = "resumed"
    STOPPED = "stopped"
    ADDED_TO_QUEUE = "added_to_queue"


# ─────────────────────────────────────────────────────────────────────────────
# ALEX JONES BROADCAST ENGINE
# ─────────────────────────────────────────────────────────────────────────────
# Tone: unfiltered Alex Jones / InfoWars / resistance broadcaster energy.
# Each event is a pool of interchangeable lines. To add variety, append more
# templates to the pool. To add a new feature, add a constant above and a pool
# below, then call say(PersonaEvents.YOUR_EVENT) from the code.
# ─────────────────────────────────────────────────────────────────────────────

_PERSONA_ENGINE: dict[str, PersonaPool] = {
    # ── STATUS ───────────────────────────────────────────────────────────────
    PersonaEvents.STATUS_IDLE: PersonaPool(
        description="Bot status when nothing is playing",
        templates=(
            "the globalists | /play to resist",
            "the deep state | /play",
            "silent broadcasts | /play",
            "1776 will commence again",
            "off the air but not off the grid",
            "waiting for the next transmission",
            "the signal is quiet. Too quiet.",
            "scanning for enemy frequencies",
            "the resistance is on standby",
            "tuning the broadcast array",
            "the globalists think they've won",
            "patriots are asleep. Wake them up with /play",
            "the truth is loading...",
            "broadcast booth is empty",
        ),
    ),
    PersonaEvents.STATUS_PLAYING: PersonaPool(
        description="Bot status when a song is playing",
        required_keys=("title",),
        templates=(
            "the truth about {title}",
            "resistance frequencies: {title}",
            "classified audio: {title}",
            "broadcasting {title}",
            "decoding {title}",
            "patriots are listening to {title}",
            "the signal is strong: {title}",
            "on air with {title}",
            "the globalists don't want you to hear {title}",
            "breaking the conditioning with {title}",
            "interdimensional transmission: {title}",
            "we got the documents: {title}",
            "1776 mode: {title}",
            "the people need to hear {title}",
        ),
    ),

    # ── PLAYBACK LIFECYCLE ────────────────────────────────────────────────────
    PersonaEvents.SONG_STARTED: PersonaPool(
        description="When audio actually begins output",
        templates=(
            "The broadcast is live, patriots.",
            "Signal locked. We are on air.",
            "The globalists can't stop this one.",
            "Transmission engaged.",
            "Audio is flowing. The truth is out.",
            "We're live on the resistance frequency.",
            "The signal is hot. Stay tuned.",
            "Broadcast booth audio confirmed.",
            "The deep state just lost this round.",
            "Patriots, we are transmitting.",
        ),
    ),
    PersonaEvents.SONG_FINISHED: PersonaPool(
        description="When a song ends naturally",
        templates=(
            "That transmission is complete.",
            "Track cleared. The message was sent.",
            "One down. The resistance continues.",
            "Signal faded. Next up.",
            "The broadcast of that track is over.",
            "Transmission archived. Moving on.",
            "The truth from that one has been delivered.",
            "The signal moved on. The fight doesn't.",
            "That song is done. The resistance isn't.",
            "Audio concluded. The broadcast continues.",
        ),
    ),
    PersonaEvents.NOW_PLAYING: PersonaPool(
        description="Text response for /nowplaying",
        required_keys=("title",),
        templates=(
            "Ladies and gentlemen, we are live with {title}.",
            "The signal is strong, patriots. Broadcasting {title}.",
            "They don't want you to hear {title}, but we're playing it anyway.",
            "Breaking the conditioning with {title}.",
            "Interdimensional transmission incoming: {title}.",
            "The resistance is on air with {title}.",
            "We got the documents: {title} is now playing.",
            "The globalists are furious. {title} is live.",
            "You are the resistance. {title} is now broadcasting.",
            "1776 mode activated. Playing {title}.",
            "The broadcast booth is hot with {title}.",
            "The people demanded {title}. We delivered.",
            "Tuned in: {title}. The signal is clean.",
            "On the resistance frequency: {title}.",
        ),
    ),
    PersonaEvents.NOW_PLAYING_TITLE: PersonaPool(
        description="Embed title for now-playing",
        templates=(
            "ON AIR",
            "BROADCASTING LIVE",
            "RESISTANCE FREQUENCY",
            "TRANSMISSION ACTIVE",
            "THE TRUTH IS PLAYING",
            "LIVE BROADCAST",
            "RESISTANCE RADIO",
            "CLASSIFIED AUDIO",
            "PATRIOT FREQUENCY",
            "THE BOOTH IS HOT",
        ),
    ),
    PersonaEvents.NOW_PLAYING_FOOTER: PersonaPool(
        description="Embed footer for now-playing",
        templates=(
            "The globalists don't want you listening to this.",
            "The signal is strong.",
            "Stay tuned, patriots.",
            "They can't jam this frequency.",
            "The truth keeps broadcasting.",
            "Resistance audio certified.",
            "The deep state hates this track.",
            "You are the resistance.",
            "Keep the signal alive.",
            "The broadcast cannot be silenced.",
        ),
    ),
    PersonaEvents.QUEUED: PersonaPool(
        description="Single song queued",
        required_keys=("title",),
        templates=(
            "Locked into the battle plan: {title}.",
            "The resistance just got louder. {title} is queued.",
            "Added {title} to the stack. The truth is multiplying.",
            "{title} is warming up in the bunker.",
            "Another transmission loaded: {title}.",
            "Arsenal updated: {title} is locked and loaded.",
            "Queued up {title}. The deep state is already sweating.",
            "{title} is in the chamber, patriots.",
            "{title} has been added to the resistance playlist.",
            "The stack grows. {title} is queued.",
            "New target acquired: {title}.",
            "{title} is locked in the queue.",
            "The arsenal grows: {title}.",
        ),
    ),
    PersonaEvents.QUEUED_TITLE: PersonaPool(
        description="Embed title for queued song",
        required_keys=("position",),
        templates=(
            "LOCKED AND LOADED — POSITION #{position}",
            "IN THE CHAMBER — #{position}",
            "QUEUED — POSITION #{position}",
            "BATTLE PLAN — #{position}",
            "ARMED — POSITION #{position}",
            "STACKED — #{position}",
            "TRANSMISSION #{position} READY",
            "RESISTANCE LINEUP — #{position}",
        ),
    ),
    PersonaEvents.QUEUED_FOOTER: PersonaPool(
        description="Embed footer for queued song",
        templates=(
            "They can't stop the signal.",
            "The arsenal is stocked.",
            "The deep state is taking notes.",
            "The resistance is organized.",
            "Queue it and they will listen.",
            "One more round in the magazine.",
            "The truth is multiplying.",
            "Stay armed, patriots.",
        ),
    ),
    PersonaEvents.QUEUED_MULTIPLE: PersonaPool(
        description="Multiple songs queued at once",
        required_keys=("count",),
        templates=(
            "Locked and loaded {count} transmissions into the battle plan.",
            "The deep state is shaking: {count} songs added to the queue.",
            "Arsenal expanded by {count} tracks. The information war continues.",
            "Loaded {count} songs. The signal is getting stronger.",
            "We got {count} more transmissions ready to roll.",
            "{count} new tracks are locked in the resistance stack.",
            "The magazine just got {count} rounds heavier.",
            "{count} songs queued. The broadcast is about to intensify.",
            "Added {count} transmissions to the playlist.",
            "The people will hear all {count} of these.",
        ),
    ),
    PersonaEvents.PLAYNEXT: PersonaPool(
        description="Song inserted at front of queue",
        required_keys=("title",),
        templates=(
            "Cutting the line, patriots. {title} is up next.",
            "Priority transmission: {title} goes to the front.",
            "The people need this now. {title} is next.",
            "Emergency broadcast: {title} moved to position one.",
            "Skipping the queue. {title} is coming up hot.",
            "{title} just bypassed the whole stack.",
            "Front of the line: {title}. The resistance comes first.",
            "Priority target acquired: {title}.",
            "{title} is now the tip of the spear.",
            "The bunker is playing {title} next.",
        ),
    ),
    PersonaEvents.PLAYNEXT_MULTIPLE: PersonaPool(
        description="Multiple songs inserted at front",
        required_keys=("count",),
        templates=(
            "Cutting the line with {count} transmissions. The front just got reinforced.",
            "Priority load complete. {count} songs moved to the front of the battle plan.",
            "The people need this now. {count} tracks jumped the queue.",
            "Emergency broadcast: {count} songs inserted at position one.",
            "{count} tracks just bypassed the whole stack.",
            "The front line now has {count} new transmissions.",
            "Priority insertion: {count} songs. The deep state is sweating.",
            "The spear tip just got {count} tracks sharper.",
        ),
    ),
    PersonaEvents.PLAYLIST_LOADED: PersonaPool(
        description="A playlist URL was loaded",
        required_keys=("count",),
        templates=(
            "Playlist locked. {count} tracks are stocked in the arsenal.",
            "Loaded the whole magazine: {count} rounds, patriots.",
            "{count} transmissions incoming.",
            "The deep state is about to get {count} tracks of truth.",
            "Playlist loaded: {count} tracks ready to roll.",
            "We got {count} transmissions in the playlist. Fire at will.",
            "The resistance playlist is locked and loaded with {count} tracks.",
            "{count} tracks in the playlist. The signal is about to be relentless.",
            "The globalists are not ready for these {count} tracks.",
            "Arsenal expanded by {count} playlist tracks.",
        ),
    ),
    PersonaEvents.SEARCHING: PersonaPool(
        description="While a search query is running",
        templates=(
            "Scanning the airwaves...",
            "Digging through the censored archives...",
            "The resistance intelligence desk is on it...",
            "Tracking the signal...",
            "Hunting the transmission...",
            "Searching the unfiltered database...",
            "The deep state doesn't want us to find this...",
            "Patriots, we're searching now...",
            "The resistance algorithm is scanning...",
            "Looking for the target...",
        ),
    ),
    PersonaEvents.SEARCH_RESULTS: PersonaPool(
        description="Search results returned",
        required_keys=("count",),
        templates=(
            "Found {count} transmissions. Pick one before the censors catch on.",
            "The search came back with {count} hot results. Choose carefully.",
            "{count} targets acquired.",
            "We got {count} signals. Lock one in.",
            "The archives returned {count} results. Make it count.",
            "Choose one of {count} transmissions, patriot.",
            "{count} possible broadcasts found. Select the truth.",
            "The resistance search found {count} tracks. Pick one.",
            "Here's what the censors missed: {count} results.",
            "Target list: {count} entries. Choose wisely.",
        ),
    ),

    # ── QUEUE CONTROL ────────────────────────────────────────────────────────
    PersonaEvents.SKIPPED: PersonaPool(
        description="After /skip",
        templates=(
            "The people have spoken. Moving on.",
            "Next transmission. The globalists couldn't stop us.",
            "Skipped. The signal cannot be silenced.",
            "Onward, patriots. The information war continues.",
            "That one's done. The resistance presses forward.",
            "Track skipped. The broadcast continues.",
            "The next truth is loading.",
            "We moved past that one. Keep fighting.",
            "Skipped. The deep state wanted you to hear that one.",
            "The people skipped that transmission.",
        ),
    ),
    PersonaEvents.SKIPTO: PersonaPool(
        description="After /skipto",
        required_keys=("position",),
        templates=(
            "Jumping to position {position}. The deep state never saw this coming.",
            "Warping to track {position}. Full speed ahead.",
            "Skipping ahead to {position}. The resistance is on a mission.",
            "Position {position} is now live. The plan has changed.",
            "We just warped to position {position}.",
            "Battle plan updated. Position {position} is hot.",
            "The people demanded position {position}. We delivered.",
            "Track {position} is now the active transmission.",
            "We skipped the filler. Position {position} is live.",
            "The resistance is moving to position {position}.",
        ),
    ),
    PersonaEvents.SHUFFLE: PersonaPool(
        description="After /shuffle",
        templates=(
            "The deep state never saw this order coming.",
            "Queue randomized. The truth comes in unexpected patterns.",
            "Shuffled. The globalists can't predict our next move.",
            "The battle plan has been scrambled. Good luck tracking us.",
            "Queue shuffled. Randomized resistance protocol engaged.",
            "The order is now classified.",
            "The resistance playlist is now unpredictable.",
            "Shuffled. Even we don't know what's next.",
            "The deep state algorithms can't follow this queue.",
            "The stack has been randomized for operational security.",
        ),
    ),
    PersonaEvents.REMOVED: PersonaPool(
        description="After /remove",
        required_keys=("title",),
        templates=(
            "Eliminated from the battle plan: {title}.",
            "{title} cut from the resistance lineup.",
            "Removed {title}. The stack is tighter now.",
            "{title} has been scrubbed from the queue.",
            "The people vetoed {title}.",
            "{title} is out of the arsenal.",
            "{title} removed. The mission is more focused.",
            "{title} has been redacted from the playlist.",
            "The resistance doesn't need {title} anymore.",
            "{title} deleted. The stack is cleaner.",
        ),
    ),
    PersonaEvents.CLEARED: PersonaPool(
        description="After /clear",
        templates=(
            "Battle plan purged. Starting fresh.",
            "Queue cleared. The resistance rebuilds.",
            "The stack is empty. New mission loading.",
            "The playlist has been wiped clean.",
            "Cleared. Time to re-arm.",
            "The queue is gone. The battlefield is quiet.",
            "The resistance stack is empty. Reload.",
            "All queued transmissions cancelled.",
            "The magazine is empty. Feed it.",
            "Queue cleared. A clean slate for the truth.",
        ),
    ),
    PersonaEvents.LOOP_ONE: PersonaPool(
        description="Loop current song enabled",
        templates=(
            "On repeat until the truth sets you free.",
            "Looping the current transmission. The message must be heard.",
            "This one stays on. Repeat mode engaged.",
            "The current track is on loop. The globalists can't skip it.",
            "Loop one engaged. The truth will repeat.",
            "This transmission is going to play again. And again.",
            "The people need to hear this one twice.",
            "Loop mode: one. The message is too important.",
        ),
    ),
    PersonaEvents.LOOP_QUEUE: PersonaPool(
        description="Loop whole queue enabled",
        templates=(
            "The entire battle plan is on loop.",
            "Queue loop engaged. Endless transmission.",
            "The signal will repeat. The resistance never stops.",
            "The whole stack is looping. The broadcast never ends.",
            "Queue loop on. The arsenal keeps firing.",
            "The resistance playlist is now infinite.",
            "The truth will repeat until the globalists fall.",
            "Loop mode: queue. The broadcast is unstoppable.",
        ),
    ),
    PersonaEvents.LOOP_OFF: PersonaPool(
        description="Loop disabled",
        templates=(
            "Loop protocol disabled. Moving forward.",
            "Loop off. New transmissions incoming.",
            "Repeat mode disengaged. The plan advances.",
            "The playlist will play once and move on.",
            "Loop cancelled. The resistance keeps advancing.",
            "No more repeats. The truth is moving forward.",
            "Loop disengaged. The broadcast continues linearly.",
            "Repeat mode off. Next mission loading.",
        ),
    ),
    PersonaEvents.QUEUE_EMPTY: PersonaPool(
        description="When the queue is empty",
        templates=(
            "The transmission has ended. The queue is empty.",
            "Battle plan is clear. Use /play to reload the arsenal.",
            "Out of ammo. Queue me up something good.",
            "The resistance has gone quiet. Time to re-arm.",
            "The queue is empty. The broadcast booth is silent.",
            "No tracks loaded. The signal is dead.",
            "The arsenal is empty. Feed it.",
            "The resistance needs new transmissions.",
            "Queue cleared. The people need more audio.",
            "The stack is empty. The globalists are celebrating.",
        ),
    ),
    PersonaEvents.QUEUE_SHOWING: PersonaPool(
        description="Title for /queue embed",
        templates=(
            "THE BATTLE PLAN",
            "RESISTANCE LINEUP",
            "THE ARSENAL",
            "UPCOMING TRANSMISSIONS",
            "THE STACK",
            "BROADCAST SCHEDULE",
            "MISSION BRIEFING",
            "OPERATION PLAYLIST",
            "THE TRUTH QUEUE",
            "RESISTANCE ROSTER",
        ),
    ),
    PersonaEvents.QUEUE_FOOTER: PersonaPool(
        description="Footer for /queue embed",
        templates=(
            "The resistance is organized.",
            "The deep state is taking notes.",
            "The signal is planned.",
            "Stay armed, patriots.",
            "The truth is queued.",
            "The broadcast is ready.",
            "The arsenal is accounted for.",
            "The people will hear all of it.",
        ),
    ),

    # ── BOT MOVEMENT ─────────────────────────────────────────────────────────
    PersonaEvents.JOINED_VC: PersonaPool(
        description="When the bot joins a voice channel",
        templates=(
            "The broadcast station is live.",
            "Connected to the channel. The signal is clear.",
            "We're in the booth. Let's go.",
            "The resistance has entered the voice channel.",
            "Broadcast booth established.",
            "The transmitter is online.",
            "Voice channel secured. The signal can flow.",
            "The resistance has a base of operations.",
            "The broadcast array is deployed.",
            "We're in. Time to wake the patriots.",
        ),
    ),
    PersonaEvents.LEFT_VC: PersonaPool(
        description="When the bot leaves a voice channel",
        templates=(
            "Going dark.",
            "Booth evacuated.",
            "The broadcast station is relocating.",
            "Signal moving to a secure location.",
            "The resistance has left the channel.",
            "Broadcast booth disconnected.",
            "The transmitter is moving.",
            "We're out. The signal will return.",
            "Voice channel cleared. The resistance reconvenes.",
            "The broadcast station is offline here.",
        ),
    ),
    PersonaEvents.MOVED_VC: PersonaPool(
        description="When the bot moves voice channels",
        templates=(
            "Relocating the transmitter.",
            "Moving the broadcast booth.",
            "The resistance follows the people.",
            "Broadcast station is changing position.",
            "The signal is moving to a new channel.",
            "Relocating for better reception.",
            "The resistance has moved operations.",
            "The booth is on the move.",
            "Transmitter relocation in progress.",
            "The broadcast is now coming from a new channel.",
        ),
    ),
    PersonaEvents.DISCONNECT_EMPTY: PersonaPool(
        description="Auto-disconnect when channel empties",
        templates=(
            "The last patriot left. Disconnecting.",
            "Voice channel empty. The resistance reconvenes elsewhere.",
            "No one left to hear the truth. Going offline.",
            "The booth is empty. Shutting down.",
            "All patriots have evacuated. Disconnecting.",
            "The signal is leaving with the people.",
            "Empty channel. The broadcast can't continue.",
            "The resistance has left the building.",
            "No audience. The transmitter is going dark.",
            "The last listener left. Signing off.",
        ),
    ),

    # ── ERRORS ───────────────────────────────────────────────────────────────
    PersonaEvents.NOTHING_PLAYING: PersonaPool(
        description="When no song is active",
        templates=(
            "There's nothing playing. The globalists already silenced us.",
            "Silent feed. Nothing is on air right now.",
            "No active transmission. The queue is dead.",
            "The broadcast booth is empty, patriots.",
            "The signal is offline. Queue something.",
            "No audio. The resistance has been quieted.",
            "The broadcast is dead. Use /play.",
            "Nothing on the airwaves. The globalists love this.",
            "The transmitter is silent. Feed it.",
            "No transmission. The booth is empty.",
        ),
    ),
    PersonaEvents.NOT_PAUSED: PersonaPool(
        description="When /resume is used but nothing is paused",
        templates=(
            "Nothing is paused. Full transmission already in progress.",
            "The signal is live. No pause to resume.",
            "Already rolling. Can't resume what isn't paused.",
            "The broadcast is active. Nothing to resume.",
            "No pause detected. The signal is already hot.",
            "The truth is already flowing. No resume needed.",
            "The booth is rolling. Can't resume.",
            "Transmission is live. Pause it first.",
            "No suspended broadcast found.",
            "The signal is on. What are you resuming?",
        ),
    ),
    PersonaEvents.ALREADY_PLAYING: PersonaPool(
        description="When /retry is used but already playing",
        templates=(
            "A song is already playing. Use /skip first if you want to change it.",
            "The broadcast booth is occupied. Skip the current track first.",
            "The signal is already live. Can't retry.",
            "The transmitter is active. Skip to retry.",
            "The booth is busy. Use /skip first.",
            "A transmission is already on air.",
            "The current broadcast is still running.",
            "The signal is occupied. Clear it first.",
            "The resistance is already broadcasting.",
            "Can't retry while a track is live.",
        ),
    ),
    PersonaEvents.INVALID_POSITION: PersonaPool(
        description="When a position argument is out of range",
        required_keys=("position",),
        templates=(
            "Position {position} doesn't exist in the battle plan.",
            "Invalid position {position}. Check the queue and try again.",
            "Slot {position} is empty. The numbers don't lie.",
            "Position {position} is out of range. The battle plan doesn't have that.",
            "The resistance stack isn't {position} tracks deep.",
            "Number {position} doesn't exist. Count again.",
            "The queue doesn't reach position {position}.",
            "Invalid coordinate {position}. Re-check the lineup.",
            "The arsenal doesn't have a slot {position}.",
            "Position {position} is outside the resistance perimeter.",
        ),
    ),
    PersonaEvents.NO_VOICE_CHANNEL: PersonaPool(
        description="When user is not in a voice channel",
        templates=(
            "You are not in a voice channel. Get in there and fight back.",
            "Join a voice channel first. The resistance needs a base.",
            "The broadcast booth needs a voice channel. Get in one.",
            "Can't transmit into thin air. Join a channel.",
            "The signal needs a target. Join a voice channel.",
            "No voice channel detected. The resistance is mobile.",
            "Get in a booth first, patriot.",
            "The transmitter needs a voice channel to broadcast.",
            "You can't run the broadcast from outside the channel.",
            "Join the resistance in a voice channel first.",
        ),
    ),
    PersonaEvents.WRONG_VOICE_CHANNEL: PersonaPool(
        description="When user is in a different voice channel",
        templates=(
            "You must be in the same voice channel to control the broadcast.",
            "Wrong channel. Get in the booth with the rest of us.",
            "The broadcast controls are in the other channel.",
            "Can't control the transmitter from over there.",
            "Get in the same booth as the bot, patriot.",
            "The resistance controls are channel-locked.",
            "Wrong booth. Move to the bot's channel.",
            "The signal is broadcast elsewhere. Join us.",
            "You're in the wrong resistance channel.",
            "Control the broadcast from the same channel.",
        ),
    ),
    PersonaEvents.OFFLINE: PersonaPool(
        description="When controls are used but bot is not connected",
        templates=(
            "The transmission is offline.",
            "No active broadcast. Nothing to control.",
            "The booth is empty. No broadcast to control.",
            "The signal is not live. Can't do that.",
            "The transmitter is offline. Start /play first.",
            "No broadcast detected. The controls are dead.",
            "The resistance is not broadcasting right now.",
            "The signal is dark. Nothing to control.",
            "The broadcast booth is empty.",
            "The transmitter is not connected.",
        ),
    ),
    PersonaEvents.NO_RESULTS: PersonaPool(
        description="When a search returns nothing",
        templates=(
            "The globalists scrubbed it. Nothing found for that query.",
            "They don't want you to hear it. No results.",
            "Signal blocked. Couldn't find anything matching that.",
            "The search came back empty. The censors are working overtime.",
            "Nothing found. The deep state buried it.",
            "The archives are clean. Too clean. No results.",
            "The resistance search turned up nothing.",
            "That query is censored. No results.",
            "The signal is not in the database. Try another.",
            "The globalists removed that one. No results.",
        ),
    ),
    PersonaEvents.YT_DLP_ERROR: PersonaPool(
        description="When yt-dlp fails to extract",
        templates=(
            "The globalists jammed the signal. YouTube is fighting back.",
            "Transmission failed. The enemy is blocking the source.",
            "The pipeline is compromised. yt-dlp couldn't pull the audio.",
            "They're suppressing the signal. Error during lookup.",
            "The extraction team took fire. yt-dlp failed.",
            "The source is under attack. Couldn't extract.",
            "YouTube locked the vault. yt-dlp couldn't get in.",
            "The enemy is jamming the audio pipeline.",
            "The resistance scouts couldn't retrieve that one.",
            "The signal source is compromised. Try again.",
        ),
    ),
    PersonaEvents.GENERIC_ERROR: PersonaPool(
        description="Fallback for unexpected errors",
        templates=(
            "The transmission hit interference.",
            "Signal compromised. Try again.",
            "Something went dark on our end.",
            "The globalists are messing with the hardware.",
            "The broadcast booth malfunctioned. Retry.",
            "The resistance equipment hiccuped. Try again.",
            "The signal took a hit. Re-engage.",
            "Unknown interference. The transmission failed.",
            "The deep state deployed a countermeasure. Retry.",
            "The resistance broadcast hit a snag. Try again.",
        ),
    ),

    # ── UTILITY ──────────────────────────────────────────────────────────────
    PersonaEvents.HELP: PersonaPool(
        description="Description for /help embed",
        templates=(
            "Here is the resistance playbook. Use it wisely.",
            "Command manual for the information war.",
            "The globalists don't want you reading this.",
            "The resistance operations manual.",
            "Everything you need to run the broadcast.",
            "The patriots' command reference.",
            "Study this. The deep state doesn't want you to.",
            "The broadcast booth handbook.",
            "Resistance command protocols.",
            "The truth about the commands. Read it.",
        ),
    ),
    PersonaEvents.HELP_TITLE: PersonaPool(
        description="Title for /help embed",
        templates=(
            "RESISTANCE PLAYBOOK",
            "COMMAND MANUAL",
            "BROADCAST BOOTH HANDBOOK",
            "RESISTANCE PROTOCOLS",
            "OPERATIONS GUIDE",
            "THE TRUTH ABOUT COMMANDS",
            "PATRIOT COMMAND LIST",
            "INFORMATION WAR MANUAL",
            "RESISTANCE FIELD GUIDE",
            "THE PLAYBOOK",
        ),
    ),
    PersonaEvents.HELP_FOOTER: PersonaPool(
        description="Footer for /help embed",
        templates=(
            "Use these commands to keep the signal alive.",
            "The resistance is only as strong as its operators.",
            "Keep the broadcast going, patriots.",
            "The truth depends on these commands.",
            "Use them wisely. The globalists are watching.",
            "The signal must survive.",
            "Stay armed with knowledge.",
            "The resistance playbook is in your hands.",
        ),
    ),
    PersonaEvents.RETRY: PersonaPool(
        description="After /retry",
        required_keys=("title",),
        templates=(
            "Retrying {title}. The resistance doesn't give up.",
            "Going again on {title}. They can't break the signal.",
            "Round two for {title}. The truth is persistent.",
            "Re-engaging {title}. The globalists jammed it once. Not twice.",
            "The signal for {title} is being reacquired.",
            "We don't retreat. We retry {title}.",
            "{title} is coming back online. The resistance retries.",
            "The truth about {title} will get through.",
            "Reloading {title}. The fight continues.",
            "{title} is being retransmitted.",
        ),
    ),
    PersonaEvents.PAUSED: PersonaPool(
        description="After /pause",
        templates=(
            "Broadcast paused. Catching our breath before the next assault.",
            "Paused. The truth can wait, but not for long.",
            "Hold the line. We're paused.",
            "Transmission suspended temporarily. Stay ready.",
            "The signal is on standby.",
            "Broadcast paused. The deep state thinks they have a moment.",
            "The resistance takes a breath. Paused.",
            "Audio paused. The fight is not.",
            "The transmission is suspended. Stay armed.",
            "Paused. But we will resume.",
        ),
    ),
    PersonaEvents.RESUMED: PersonaPool(
        description="After /resume",
        templates=(
            "We're back on air. They tried to stop us. They failed.",
            "Broadcast resumed. The signal is stronger than ever.",
            "Back in the fight. The resistance continues.",
            "Audio restored. The truth keeps flowing.",
            "The signal is back. The globalists are furious.",
            "Transmission resumed. No pause can stop the truth.",
            "We're rolling again. The resistance is live.",
            "The broadcast booth is back online.",
            "Audio re-engaged. The signal persists.",
            "The resistance never stays paused for long.",
        ),
    ),
    PersonaEvents.STOPPED: PersonaPool(
        description="After /stop",
        templates=(
            "Going dark. Disconnecting from the grid.",
            "The broadcast is over, but we will never stop the fight.",
            "Off air. The globalists think they won. They didn't.",
            "Transmission terminated. The resistance will return.",
            "Going silent. 1776 will commence again.",
            "The broadcast booth is shutting down.",
            "The signal is going dark. For now.",
            "The resistance is off air. Temporarily.",
            "The transmission has been terminated.",
            "The broadcast is stopped. The fight is not.",
        ),
    ),
    PersonaEvents.ADDED_TO_QUEUE: PersonaPool(
        description="Generic single-song added",
        required_keys=("title",),
        templates=(
            "Added {title} to the battle plan.",
            "{title} is locked in the queue.",
            "The arsenal grows: {title}.",
            "{title} is now part of the resistance stack.",
            "The people get to hear {title}.",
            "{title} has been loaded into the magazine.",
            "The broadcast will include {title}.",
            "{title} is in the queue. The truth expands.",
            "The resistance playlist now includes {title}.",
            "{title} is queued for the information war.",
        ),
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# NEUTRAL FALLBACKS (when PERSONA_ENABLED is False)
# ─────────────────────────────────────────────────────────────────────────────

_NEUTRAL: dict[str, str] = {
    PersonaEvents.STATUS_IDLE: "the globalists | /play to resist",
    PersonaEvents.STATUS_PLAYING: "{title}",
    PersonaEvents.SONG_STARTED: "Audio started.",
    PersonaEvents.SONG_FINISHED: "Track finished.",
    PersonaEvents.NOW_PLAYING: "Now playing: {title}",
    PersonaEvents.NOW_PLAYING_TITLE: "Now Playing",
    PersonaEvents.NOW_PLAYING_FOOTER: "Keep listening.",
    PersonaEvents.QUEUED: "Added {title} to the queue.",
    PersonaEvents.QUEUED_TITLE: "Queued — Position #{position}",
    PersonaEvents.QUEUED_FOOTER: "Locked in.",
    PersonaEvents.QUEUED_MULTIPLE: "Added {count} songs to the queue.",
    PersonaEvents.PLAYNEXT: "{title} will play next.",
    PersonaEvents.PLAYNEXT_MULTIPLE: "{count} songs will play next.",
    PersonaEvents.PLAYLIST_LOADED: "Loaded {count} songs.",
    PersonaEvents.SEARCHING: "Searching...",
    PersonaEvents.SEARCH_RESULTS: "Found {count} results.",
    PersonaEvents.SKIPPED: "Skipped.",
    PersonaEvents.SKIPTO: "Skipped to position {position}.",
    PersonaEvents.SHUFFLE: "Queue shuffled.",
    PersonaEvents.REMOVED: "Removed {title}.",
    PersonaEvents.CLEARED: "Queue cleared.",
    PersonaEvents.LOOP_ONE: "Looping current song.",
    PersonaEvents.LOOP_QUEUE: "Looping queue.",
    PersonaEvents.LOOP_OFF: "Loop disabled.",
    PersonaEvents.QUEUE_EMPTY: "The queue is empty.",
    PersonaEvents.QUEUE_SHOWING: "Queue",
    PersonaEvents.QUEUE_FOOTER: "Total upcoming time displayed.",
    PersonaEvents.JOINED_VC: "Connected to voice channel.",
    PersonaEvents.LEFT_VC: "Disconnected.",
    PersonaEvents.MOVED_VC: "Moved voice channel.",
    PersonaEvents.DISCONNECT_EMPTY: "Disconnected due to empty channel.",
    PersonaEvents.NOTHING_PLAYING: "Nothing is playing.",
    PersonaEvents.NOT_PAUSED: "Nothing is paused.",
    PersonaEvents.ALREADY_PLAYING: "Already playing.",
    PersonaEvents.INVALID_POSITION: "Invalid position.",
    PersonaEvents.NO_VOICE_CHANNEL: "Join a voice channel first.",
    PersonaEvents.WRONG_VOICE_CHANNEL: "You must be in the same voice channel.",
    PersonaEvents.OFFLINE: "No active broadcast.",
    PersonaEvents.NO_RESULTS: "No results found.",
    PersonaEvents.YT_DLP_ERROR: "Error looking up media.",
    PersonaEvents.GENERIC_ERROR: "An error occurred.",
    PersonaEvents.HELP: "Command list.",
    PersonaEvents.HELP_TITLE: "Help",
    PersonaEvents.HELP_FOOTER: "Use these commands to control the bot.",
    PersonaEvents.RETRY: "Retrying {title}.",
    PersonaEvents.PAUSED: "Paused.",
    PersonaEvents.RESUMED: "Resumed.",
    PersonaEvents.STOPPED: "Stopped.",
    PersonaEvents.ADDED_TO_QUEUE: "Added {title}.",
}


# ─────────────────────────────────────────────────────────────────────────────
# FORMATTING HELPERS
# ─────────────────────────────────────────────────────────────────────────────

class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def _extract_placeholders(template: str) -> set[str]:
    """Return the set of placeholder names used in a template string."""
    # Simple parser for {name} placeholders.
    placeholders = set()
    current = 0
    while True:
        start = template.find("{", current)
        if start == -1:
            break
        end = template.find("}", start)
        if end == -1:
            break
        key = template[start + 1 : end]
        if key and not key.startswith("{"):
            placeholders.add(key)
        current = end + 1
    return placeholders


def _format(template: str, **kwargs) -> str:
    return template.format_map(_SafeDict(kwargs))


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def _say_template(event: str, **kwargs) -> str | None:
    """Pick a template for an event, falling back to neutral when persona is disabled."""
    if PERSONA_ENABLED:
        pool = _PERSONA_ENGINE.get(event)
        if pool and pool.templates:
            return random.choice(pool.templates)
        return None

    neutral = _NEUTRAL.get(event)
    if neutral is not None:
        return neutral
    return None


def say(event: str, **kwargs) -> str:
    """Return a random formatted line for the given event."""
    template = _say_template(event, **kwargs)
    if template is None:
        return ""
    return _format(template, **kwargs)


def say_embed(event: str, **kwargs) -> tuple[str, str | None, str | None]:
    """Return (title, description, footer) for a multi-part embed.

    Looks for title/footer variants by appending _TITLE and _FOOTER to the event.
    Description is taken from the event itself.
    """
    title_template = _say_template(f"{event}_title", **kwargs)
    desc_template = _say_template(event, **kwargs)
    footer_template = _say_template(f"{event}_footer", **kwargs)

    title = _format(title_template, **kwargs) if title_template else ""
    description = _format(desc_template, **kwargs) if desc_template else ""
    footer = _format(footer_template, **kwargs) if footer_template else None
    return title, description, footer


def say_status(playing_title: str | None = None) -> discord.Activity:
    """Return a randomized Discord activity."""
    if playing_title:
        template = _say_template(PersonaEvents.STATUS_PLAYING, title=playing_title)
    else:
        template = _say_template(PersonaEvents.STATUS_IDLE)
    if template is None:
        template = "music" if playing_title else "idle"
    text = _format(template, title=playing_title or "")
    return discord.Activity(type=discord.ActivityType.listening, name=text)


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def validate_persona() -> list[str]:
    """Return a list of validation issues in the persona engine."""
    issues = []
    event_names = {value for name, value in vars(PersonaEvents).items() if not name.startswith("_")}

    for event_name in event_names:
        pool = _PERSONA_ENGINE.get(event_name)
        if pool is None:
            issues.append(f"Missing pool for event: {event_name}")
            continue
        if not pool.templates:
            issues.append(f"Empty template pool for event: {event_name}")
            continue

        required = set(pool.required_keys)
        for template in pool.templates:
            placeholders = _extract_placeholders(template)
            missing = required - placeholders
            extra = placeholders - required
            if missing:
                issues.append(
                    f"Event '{event_name}' template missing required keys: {missing!r}"
                )
            if extra:
                # Extra placeholders are not necessarily errors, but warn in case.
                issues.append(
                    f"Event '{event_name}' template has unused placeholders: {extra!r}"
                )

    return issues


def _register_default_events():
    """Ensure no placeholder events are forgotten. This is a no-op for the static registry.

    Reserved for future dynamic event registration.
    """
    pass


_register_default_events()
