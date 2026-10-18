"""The CSV validator: accepts good data, rejects every listed kind of bad data."""
import csv
import shutil

import pytest

from src import config
from src.data_loader import build_matrix_from_sources, load_dataset, validate_dataset


@pytest.fixture
def data_copy(tmp_path):
    """A writable copy of the real dataset."""
    dst = tmp_path / "data"
    shutil.copytree(config.DATA_DIR, dst)
    return dst


def _edit_matrix(folder, i, j, value):
    path = folder / config.MATRIX_FILE
    rows = list(csv.reader(path.open(encoding="utf-8")))
    rows[i + 1][j + 1] = value
    with path.open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)


def test_real_dataset_is_valid():
    ds = load_dataset(config.DATA_DIR)
    rep = validate_dataset(ds)
    assert rep.ok, rep.errors
    assert ds.n == 9 and len(ds.sources) == 72
    assert rep.status_counts == {"ACTUAL": 72}


@pytest.mark.parametrize("i,j,value,message", [
    (2, 2, "1.5", "diagonal"),
    (0, 3, "-2", "positive"),
    (0, 3, "0", "positive"),
    (4, 1, "", "blank"),
    (4, 1, "abc", "not a number"),
])
def test_bad_matrix_values_are_errors(data_copy, i, j, value, message):
    _edit_matrix(data_copy, i, j, value)
    rep = validate_dataset(load_dataset(data_copy))
    assert not rep.ok
    assert any(message in e for e in rep.errors), rep.errors


def test_non_square_matrix_is_an_error(data_copy):
    path = data_copy / config.MATRIX_FILE
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    rep = validate_dataset(load_dataset(data_copy))
    assert any("square" in e or "labels" in e for e in rep.errors)


def test_matrix_and_sources_must_agree(data_copy):
    _edit_matrix(data_copy, 0, 1, "99")
    rep = validate_dataset(load_dataset(data_copy))
    assert any("data_sources.csv says" in e for e in rep.errors)


def test_ids_must_match_locations(data_copy):
    path = data_copy / config.LOCATIONS_FILE
    text = path.read_text(encoding="utf-8").replace("\n3,V3,", "\n7,V3,")
    path.write_text(text, encoding="utf-8")
    rep = validate_dataset(load_dataset(data_copy))
    assert any("id must be 3" in e for e in rep.errors)


def test_asymmetric_pairs_and_assumed_entries_are_reported(data_copy):
    path = data_copy / config.SOURCES_FILE
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    rows[0]["status"], rows[0]["assumed_basis"] = "ASSUMED", "copied from V1->V0"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    ds = load_dataset(data_copy)
    rep = validate_dataset(ds)
    assert rep.ok, rep.errors
    assert rep.assumed_edges == [(0, 1)]
    assert rep.status_counts == {"ACTUAL": 71, "ASSUMED": 1}
    assert rep.asymmetric_pairs and all(a != b for _, _, a, b in rep.asymmetric_pairs)


def test_actual_rows_need_date_and_time(data_copy):
    path = data_copy / config.SOURCES_FILE
    path.write_text(path.read_text(encoding="utf-8").replace(",2026-10-17,", ",,"),
                    encoding="utf-8")
    rep = validate_dataset(load_dataset(data_copy))
    assert any("measured_date" in e for e in rep.errors)


def test_build_matrix_from_sources_round_trip(data_copy):
    before = (data_copy / config.MATRIX_FILE).read_text(encoding="utf-8")
    (data_copy / config.MATRIX_FILE).unlink()
    build_matrix_from_sources(data_copy)
    ds = load_dataset(data_copy)
    assert validate_dataset(ds).ok
    assert [r.split(",")[1:] for r in before.split()] == \
           [r.split(",")[1:] for r in (data_copy / config.MATRIX_FILE).read_text().split()]
