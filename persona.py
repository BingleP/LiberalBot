import random
from collections import defaultdict


_QUOTES = {
    "now_playing": [
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
    ],
    "queued": [
        "Locked into the battle plan: {title}.",
        "The resistance just got louder. {title} is queued.",
        "Added {title} to the stack. The truth is multiplying.",
        "{title} is warming up in the bunker.",
        "Another transmission loaded: {title}.",
        "Arsenal updated: {title} is locked and loaded.",
        "Queued up {title}. The deep state is already sweating.",
        "{title} is in the chamber, patriots.",
    ],
    "queued_multiple": [
        "Locked and loaded {count} transmissions into the battle plan.",
        "The deep state is shaking: {count} songs added to the queue.",
        "Arsenal expanded by {count} tracks. The information war continues.",
        "Loaded {count} songs. The signal is getting stronger.",
        "We got {count} more transmissions ready to roll.",
    ],
    "playnext": [
        "Cutting the line, patriots. {title} is up next.",
        "Priority transmission: {title} goes to the front.",
        "The people need this now. {title} is next.",
        "Emergency broadcast: {title} moved to position one.",
        "Skipping the queue. {title} is coming up hot.",
    ],
    "playnext_multiple": [
        "Cutting the line with {count} transmissions. The front just got reinforced.",
        "Priority load complete. {count} songs moved to the front of the battle plan.",
        "The people need this now. {count} tracks jumped the queue.",
        "Emergency broadcast: {count} songs inserted at position one.",
    ],
    "skipped": [
        "The people have spoken. Moving on.",
        "Next transmission. The globalists couldn't stop us.",
        "Skipped. The signal cannot be silenced.",
        "Onward, patriots. The information war continues.",
        "That one's done. The resistance presses forward.",
    ],
    "skipto": [
        "Jumping to position {position}. The deep state never saw this coming.",
        "Warping to track {position}. Full speed ahead.",
        "Skipping ahead to {position}. The resistance is on a mission.",
        "Position {position} is now live. The plan has changed.",
    ],
    "stopped": [
        "Going dark. Disconnecting from the grid.",
        "The broadcast is over, but we will never stop the fight.",
        "Off air. The globalists think they won. They didn't.",
        "Transmission terminated. The resistance will return.",
        "Going silent. 1776 will commence again.",
    ],
    "paused": [
        "Broadcast paused. Catching our breath before the next assault.",
        "Paused. The truth can wait, but not for long.",
        "Hold the line. We're paused.",
        "Transmission suspended temporarily. Stay ready.",
    ],
    "resumed": [
        "We're back on air. They tried to stop us. They failed.",
        "Broadcast resumed. The signal is stronger than ever.",
        "Back in the fight. The resistance continues.",
        "Audio restored. The truth keeps flowing.",
    ],
    "queue_empty": [
        "The transmission has ended. The queue is empty.",
        "Battle plan is clear. Use /play to reload the arsenal.",
        "Out of ammo. Queue me up something good.",
        "The resistance has gone quiet. Time to re-arm.",
    ],
    "shuffle": [
        "The deep state never saw this order coming.",
        "Queue randomized. The truth comes in unexpected patterns.",
        "Shuffled. The globalists can't predict our next move.",
        "The battle plan has been scrambled. Good luck tracking us.",
        "Queue shuffled. Randomized resistance protocol engaged.",
    ],
    "retry": [
        "Retrying {title}. The resistance doesn't give up.",
        "Going again on {title}. They can't break the signal.",
        "Round two for {title}. The truth is persistent.",
        "Re-engaging {title}. The globalists jammed it once. Not twice.",
    ],
    "no_results": [
        "The globalists scrubbed it. Nothing found for that query.",
        "They don't want you to hear it. No results.",
        "Signal blocked. Couldn't find anything matching that.",
        "The search came back empty. The censors are working overtime.",
    ],
    "yt_dlp_error": [
        "The globalists jammed the signal. YouTube is fighting back.",
        "Transmission failed. The enemy is blocking the source.",
        "The pipeline is compromised. yt-dlp couldn't pull the audio.",
        "They're suppressing the signal. Error during lookup.",
    ],
    "nothing_playing": [
        "There's nothing playing. The globalists already silenced us.",
        "Silent feed. Nothing is on air right now.",
        "No active transmission. The queue is dead.",
        "The broadcast booth is empty, patriots.",
    ],
    "not_paused": [
        "Nothing is paused. Full transmission already in progress.",
        "The signal is live. No pause to resume.",
        "Already rolling. Can't resume what isn't paused.",
    ],
    "disconnected": [
        "The last patriot left. Disconnecting.",
        "Voice channel empty. The resistance reconvenes elsewhere.",
        "No one left to hear the truth. Going offline.",
    ],
    "added_to_queue": [
        "Added {title} to the battle plan.",
        "{title} is locked in the queue.",
        "The arsenal grows: {title}.",
    ],
    "removed": [
        "Eliminated from the battle plan: {title}.",
        "{title} cut from the resistance lineup.",
        "Removed {title}. The stack is tighter now.",
    ],
    "cleared": [
        "Battle plan purged. Starting fresh.",
        "Queue cleared. The resistance rebuilds.",
        "The stack is empty. New mission loading.",
    ],
    "loop_one": [
        "On repeat until the truth sets you free.",
        "Looping the current transmission. The message must be heard.",
        "This one stays on. Repeat mode engaged.",
    ],
    "loop_queue": [
        "The entire battle plan is on loop.",
        "Queue loop engaged. Endless transmission.",
        "The signal will repeat. The resistance never stops.",
    ],
    "loop_off": [
        "Loop protocol disabled. Moving forward.",
        "Loop off. New transmissions incoming.",
        "Repeat mode disengaged. The plan advances.",
    ],
    "joined_vc": [
        "The broadcast station is live.",
        "Connected to the channel. The signal is clear.",
        "We're in the booth. Let's go.",
    ],
    "help": [
        "Here is the resistance playbook. Use it wisely.",
        "Command manual for the information war.",
        "The globalists don't want you reading this.",
    ],
    "invalid_position": [
        "That position doesn't exist in the battle plan.",
        "Invalid position. Check the queue and try again.",
        "That slot is empty. The numbers don't lie.",
    ],
    "already_playing": [
        "A song is already playing. Use /skip first if you want to change it.",
        "The broadcast booth is occupied. Skip the current track first.",
    ],
    "no_voice_channel": [
        "You are not in a voice channel. Get in there and fight back.",
        "Join a voice channel first. The resistance needs a base.",
    ],
    "wrong_voice_channel": [
        "You must be in the same voice channel to control the broadcast.",
        "Wrong channel. Get in the booth with the rest of us.",
    ],
    "offline": [
        "The transmission is offline.",
        "No active broadcast. Nothing to control.",
    ],
}


class _SafeDict(dict):
    def __missing__(self, key):
        return "{" + key + "}"


def say(event: str, **kwargs) -> str:
    pool = _QUOTES.get(event, [""])
    if not pool:
        return ""
    template = random.choice(pool)
    return template.format_map(_SafeDict(kwargs))
