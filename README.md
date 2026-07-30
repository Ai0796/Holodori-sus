# SUS (Sliding Universal Score) Parser for Hololive Dreams
Sliding Universal Score (Formerly SeaUrchin Score) is a universal format that denotes a sliding rhythm game format

Hololive dreams uses a slightly modified version with compressed offsets, ghost notes, and modified flick note types (flick notes are used as a dummy for nearly everything)

This program currently parses all playable notes and matches all shown notes in the metadata
- Normal notes
- Flick notes
- Slide start notes
- Slide mid notes
- Slide end notes
- Slide end flicks
- Slide relays

It does not provide a method to interface with non-playable notes
- Invisible slide relays
- Slide Bezier-curve control points
- Ghost notes

As of 7/29/2026, all songs have been verified against in game metadata
