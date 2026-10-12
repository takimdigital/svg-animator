# Typing: a terminal types lines, and swaps a word in place

**Request, in the user's words:** a dark terminal that types "Do not trust the Hype, trust your Hardware…", deletes
"ware", types "work" in its place, then types "GET SHIT DONE." Dark, direct, no hype.

**Route:** new type (`typing`), because a terminal typing effect will come up again.

**What was built:** `scripts/things_c.py` (`build_typing`), `assets/specs/typing-manifesto.json`, its example and
static twin in `assets/examples/`.

**Decisions and why:**
- *Swap in place, not reflow.* The swapped word must have the same length as the old one. Otherwise the rest of the
  line would move during the swap, which reads as a glitch, not a deletion. The type refuses different lengths.
- *The swapped source word must occur exactly once in its line.* A second match would be ambiguous about which
  letters to delete.
- *Static-first with letters as elements.* Each character is its own element. The removed letters start with base
  opacity 0 and the new letters with 1, so the still frame is the finished sentence. (An earlier version drew the
  finished sentence as a separate layer; it showed the whole line from frame 0 and hid the typing.)
- *The caret is one rectangle moved along a path of (time, x, y).* Its base position is the end of the text, so the
  still frame has a caret where typing ended.
- *Timing is derived.* Each character gets a raw time; the whole schedule is scaled into the typing window, so a
  longer line types more slowly and the loop always ends with a hold.

**Refused cases:** a swap of different lengths; a swap source that is not unique in its line. Both exit with a message
that names the fix.

**Looks:** `scanlines` and `glow` are opt-in options; the manifesto spec turns both on, and its example matches the approved hand-made file at the finished frame.

**Verified:** lint 0 errors / 0 warnings; the example regenerates byte-for-byte; frames at 1, 4, 6.6, 8.6 and 12.8 s
show typing, the red "ware", the gold "work", and the finished line; the still frame (SMIL removed) shows
"Hardwork…" and "GET SHIT DONE." with no overlap. Breaking the length check made its test fail; breaking the example
made the drift test fail; both restored.

**Not verified:** how it looks in a real browser at real speed (frames are still captures); GitHub's rendering;
font width on machines without the first font in the stack (the caret may sit a pixel off).
