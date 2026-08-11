# Provenance

Extracted without modifying the source checkout from private repository
`rikiyanai/lateletter` at observed HEAD
`fad00c6bb8f2b93faaa5c7e79cabc2b7faee77f6` on 2026-08-11.

| Standalone path | Source path | Source SHA-256 | Packaged SHA-256 |
| --- | --- | --- | --- |
| `scripts/recover_monospace_ascii.py` | `scripts/recover_monospace_ascii.py` | `0e6c29b254722704190c96103915fc901cc7e95ebeaee2bb6b51110c227c73f1` | same |
| `sample/source.normalized.png` | `tracked/LateLetterResearch/transcription-parity/horse-animation-sheet/source/source.normalized.png` | `9ea8eab2c0b378ed89ad2337515a6baea4ec81d0eace6ba042fab4abee63a3d3` | same |
| `sample/calibration.json` | `tracked/LateLetterResearch/transcription-parity/horse-animation-sheet/attempts/064-immutable-ownership-context-retry/calibration.json` | `fe22ce7075c1f12907edb2c261bb738b7800688f883d12a3903d5f4a3997242d` | `f8a1aca96ccc43a08b1981a7fff0d34ebe773f7cc45fe148178c3554d65f7944` |

The packaged calibration changes only `source_png` from the source machine's
absolute path to `sample/source.normalized.png`; the hash records that deliberate
standalone-path normalization.

The source checkout was dirty with unrelated user work. Extraction copied only
the three reviewed paths and did not stage, commit, or alter that checkout.
