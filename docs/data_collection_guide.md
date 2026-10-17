# How to collect the real data

**Fast option (chosen): OpenStreetMap routing.** On a computer with internet access:
```
python main.py --fetch-osm     # blank coordinates via Nominatim, then 72 directed distances via OSRM
python main.py --validate
```
Any place that OpenStreetMap cannot find is reported. Copy its coordinates from Google Maps (right-click the pin), paste them into `data/locations.csv`, and run `--fetch-osm` again; filled-in coordinates are never overwritten. The rest of this guide is the manual Google Maps method, kept as a fallback.


Goal: **9 vertices** (V0 = Red Cross chapter office + V1..V8 = 8 hospitals) and **72 directed driving distances** (36 pairs × 2 directions), all read from Google Maps and marked **ACTUAL**.

Time needed: about 20 min for the locations, plus 60–75 min for the distances (36 pairs at about 2 min per pair, using the ⇅ reverse button). Do all the distances in **one sitting** if you can, so every reading comes from the same day and similar traffic.

---

## Before you start
- Use **Google Maps in a desktop browser** (maps.google.com). It shows every suggested route with its distance, and it makes copying coordinates easy.
- Open the CSV files in Excel or Google Sheets. When saving from Excel, choose **"CSV UTF-8 (Comma delimited)"** so names like "Seriña" survive.
- Keep the files where they are: `tsp_sa_cdo/data/locations.csv`, `data/data_sources.csv`, `data/distance_matrix.csv`.

---

## Part 1 · The 9 locations → `data/locations.csv`

Choose 8 hospitals in Cagayan de Oro City that a blood courier would plausibly supply (hospitals with blood or transfusion services). Some well-known hospitals you could consider (**check each one on Google Maps yourself**):
Northern Mindanao Medical Center, J.R. Borja General Hospital, Capitol University Medical Center, Maria Reyna–Xavier University Hospital, Polymedic Medical Plaza, Polymedic General Hospital, Cagayan de Oro Medical Center, Sabal Hospital, Madonna and Child Hospital.

For **each** location (V0 first, then V1..V8 in any order you like):

1. Search for the place in Google Maps and click its **red pin**. For V0, search for the Philippine Red Cross Misamis Oriental chapter office and confirm the address shown on the place card.
2. **Coordinates:** right-click exactly on the pin (or on the building entrance). The first line of the menu shows the coordinates, e.g. `8.48xxx, 124.64xxx`. Click it to copy. Paste the first number into `latitude` and the second into `longitude`, keeping at least **5 decimals**.
3. **google_maps_url:** on the place card click **Share → Copy link** and paste it.
4. Fill in the other columns:

| column | what to write | example |
|---|---|---|
| `id` | already filled: 0..8 | `3` |
| `label` | already filled: V0..V8 | `V3` |
| `name` | full official name as on Google Maps | `Northern Mindanao Medical Center` |
| `short_name` | **≤ 10 characters**, used in every figure | `NMMC` |
| `role` | already filled: `depot` for V0, `stop` for the rest | `stop` |
| `address` | street and barangay | `Capitol Compound, Brgy. 23` |
| `notes` | anything useful | `pin at the main entrance` |

5. Save the file, then run this once:
   ```
   python main.py --prepare-sources
   ```
   It writes 72 rows into `data/data_sources.csv` with your short names, ordered **V0→V1, V1→V0, V0→V2, V2→V0, …**, so each pair is followed by its reverse.

---

## Part 2 · The 72 distances → `data/data_sources.csv`

Settings, kept the same for every reading:
- **Directions → car icon (Driving).**
- Departure: **"Leave now"** (the default). Record the clock time of each reading.
- Route options: leave **"Avoid highways / tolls / ferries" unticked**.
- Start and end points: use the **same places you chose in Part 1** (pick the same search result, or paste the coordinates from `locations.csv`).

For each pair, working down the file two rows at a time:

1. Set **origin = the `from` place** and **destination = the `to` place**.
2. Google shows 1–3 suggested routes, each with a time and a **distance**. Take the **shortest distance among the suggested routes**, which is not necessarily the highlighted (fastest) one.
3. Fill in the row:

| column | what to write | example |
|---|---|---|
| `distance_km` | the distance in km, as shown. Convert metres: `850 m` → `0.85` | `3.4` |
| `status` | `ACTUAL` | `ACTUAL` |
| `source` | the same text in every row | `Google Maps, driving, shortest suggested route (desktop)` |
| `measured_date` | the day of the reading, YYYY-MM-DD | `2026-10-20` |
| `measured_time` | the clock time, 24 h HH:MM | `09:42` |
| `route_summary` | the "via …" text Google shows under that route | `via Corrales Ave` |
| `assumed_basis` | leave empty for ACTUAL rows | |
| `notes` | e.g. `fastest route was 3.9 km via Velez St` | |

4. Click the **⇅ (reverse) button** to swap origin and destination. Read the **shortest suggested route again**; it is often different because of one-way streets. Fill in the next row (the reverse direction) the same way.
5. Move on to the next pair.

**Only if a direction cannot be measured** (e.g. Google gives no route): set `status` = `ASSUMED`, copy the distance of the opposite direction, and write `copied from V3->V1 (not measured)` in `assumed_basis`. Assumed cells are hatched in the matrix figure and counted on the slides.

---

## Part 3 · Build and check the matrix

```
python main.py --build-matrix    # writes data/distance_matrix.csv from data_sources.csv
python main.py --validate        # checks everything; prints errors and warnings
```

What the validator reports, and what to do about it:
- **ERROR** (the program refuses to run): a blank or non-numeric value, a non-zero diagonal, a missing row, an ACTUAL row without date or time, or a matrix that differs from `data_sources.csv`. Fix the CSV and run again.
- **WARNING: triangle-inequality breaks**: d(A,C) is more than d(A,B) + d(B,C) + 0.1 km. This can happen on real roads (one-way loops), but it is the best typo detector. Open `outputs/data_quality.csv` and re-check those readings in Google Maps.
- **Asymmetric pairs**: listed in `outputs/data_quality.csv`. Differences of a few hundred metres are normal. Re-check any difference over about 1.5 km.
- **"outside the Cagayan de Oro area"**: latitude and longitude are probably swapped.

When `--validate` prints **PASS**, tell me that the files are ready (or send them), and I will rerun everything and regenerate the figures and docs with the real numbers.

---

## Quick self-check before sending
- [ ] 9 rows in `locations.csv`; V0 is the Red Cross chapter office, with role `depot`.
- [ ] 72 rows in `data_sources.csv`, all with a distance, a status, a date and a time.
- [ ] `python main.py --validate` → **PASS**.
- [ ] Spot-check 3 random rows against Google Maps again.
