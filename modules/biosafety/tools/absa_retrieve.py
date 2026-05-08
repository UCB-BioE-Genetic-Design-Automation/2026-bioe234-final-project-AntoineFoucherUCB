import csv
import difflib
import re
from pathlib import Path


def _tokenize(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", (text or "").lower()) if len(t) > 1}


def _safe_str(row: dict, key: str) -> str:
    return str(row.get(key, "") or "").strip()


class AbsaRetrieve:
    def initiate(self) -> None:
        self.csv_path = Path(__file__).resolve().parent.parent / "data" / "absa_initial_db.csv"
        self.rows: list[dict] = []
        self.organism_index: list[str] = []
        self._loaded = False

        # Column names in this CSV use long labels with IDs.
        self.col_agent_type = "Agent Type -- 320"
        self.col_genus = "Genus / Virus Group -- 321"
        self.col_species = "Species / Virus Name -- 322"
        self.col_uid = "Unique-ID -- 354"
        self.col_item_id = "itemId"

        self.source_cols = {
            "NIH": "NIH -- 323",
            "BMBL": "BMBL -- 325",
            "Australia / New Zealand": "Australia / New Zealand -- 326",
            "Belgium": "Belgium -- 328",
            "Canada": "Canada -- 330",
            "Canada PSDS": "Canada PSDS -- 331",
            "European Community": "European Community -- 333",
            "Georgia": "Georgia -- 337",
            "Germany": "Germany -- 335",
            "Singapore": "Singapore -- 339",
            "Singapore schedule": "Singapore schedule -- 341",
            "Switzerland": "Switzerland -- 342",
            "United Kingdom": "United Kingdom -- 344",
        }

        self.note_cols = {
            "NIH": "NIH notes -- 324",
            "Australia / New Zealand": "Austrailia / New Zealand notes -- 327",
            "Belgium": "Belgium notes -- 329",
            "Canada": "Canada Notes -- 332",
            "European Community": "European Community notes -- 334",
            "Georgia": "Georgia notes -- 338",
            "Germany": "Germany notes -- 336",
            "Singapore": "Singapore notes -- 340",
            "Switzerland": "Switzerland notes -- 343",
            "United Kingdom": "United Kingdom notes -- 345",
        }

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if not self.csv_path.exists():
            self.rows = []
            self._loaded = True
            return
        with self.csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            self.rows = list(csv.DictReader(f))
        seen = set()
        organisms = []
        for row in self.rows:
            genus = self._normalize_name(_safe_str(row, self.col_genus))
            species = self._normalize_name(_safe_str(row, self.col_species))
            org = self._normalize_name(f"{genus} {species}".strip())
            if not org or org in seen:
                continue
            seen.add(org)
            organisms.append(org)
        self.organism_index = sorted(organisms)
        self._loaded = True

    def _build_row_text(self, row: dict) -> str:
        return " ".join(
            [
                _safe_str(row, self.col_agent_type),
                _safe_str(row, self.col_genus),
                _safe_str(row, self.col_species),
                _safe_str(row, self.col_uid),
            ]
        ).strip()

    def _score_row(self, query: str, q_tokens: set[str], row: dict) -> float:
        row_text = self._build_row_text(row).lower()
        row_tokens = _tokenize(row_text)
        if not row_tokens:
            return 0.0

        overlap = len(q_tokens & row_tokens)
        score = float(overlap)

        # Boost exact genus/species and full-string containment.
        genus = _safe_str(row, self.col_genus).lower()
        species = _safe_str(row, self.col_species).lower()
        full_name = f"{genus} {species}".strip()
        q = query.lower().strip()

        if q and q == full_name:
            score += 10.0
        elif q and q in full_name:
            score += 6.0
        elif q and q in row_text:
            score += 3.0

        # Small preference for rows with more source classifications available.
        populated = 0
        for col in self.source_cols.values():
            if _safe_str(row, col):
                populated += 1
        score += min(populated, 8) * 0.05
        return score

    def _normalize_name(self, text: str) -> str:
        # Preserve alphanumerics, spaces, hyphen, and period for entries like "subsp."
        t = str(text or "").strip().lower()
        t = re.sub(r"[^a-z0-9.\-\s]+", " ", t)
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _extract_sources(self, row: dict) -> dict:
        out = {}
        for source_name, col in self.source_cols.items():
            value = _safe_str(row, col)
            if not value:
                continue
            source_obj = {"value": value}
            note_col = self.note_cols.get(source_name, "")
            if note_col:
                note = _safe_str(row, note_col)
                if note:
                    source_obj["notes"] = note
            out[source_name] = source_obj
        return out

    def _suggest_names(self, q_norm: str, limit: int = 5) -> list[str]:
        if not q_norm or not self.organism_index:
            return []
        out = difflib.get_close_matches(q_norm, self.organism_index, n=limit, cutoff=0.72)
        return out

    def run(self, query: str, top_k: int = 5) -> dict:
        self._ensure_loaded()
        q = str(query or "").strip()
        if not q:
            return {"status": "error", "message": "query is required."}
        q_norm = self._normalize_name(q)
        q_parts = q_norm.split()
        if len(q_parts) < 2:
            return {
                "status": "error",
                "query": q,
                "message": "Query must include genus + species (e.g., 'streptococcus agalactiae').",
                "matches": [],
            }
        if not self.rows:
            return {
                "status": "error",
                "message": f"ABSA CSV not found or empty at {self.csv_path}",
                "matches": [],
            }

        # Strict exact matching on genus + species only (no fuzzy spillover).
        exact = []
        for idx, row in enumerate(self.rows):
            genus = self._normalize_name(_safe_str(row, self.col_genus))
            species = self._normalize_name(_safe_str(row, self.col_species))
            organism = self._normalize_name(f"{genus} {species}".strip())
            if organism == q_norm:
                exact.append((idx, row))

        if not exact:
            suggestions = self._suggest_names(q_norm, limit=5)
            return {
                "status": "not_found",
                "query": q,
                "top_k": 0,
                "match_count": 0,
                "matches": [],
                "did_you_mean": suggestions,
                "source": str(self.csv_path),
                "message": "No exact genus + species match found in ABSA CSV.",
            }

        k = max(1, min(int(top_k or 5), 25))
        matches = []
        for idx, row in exact[:k]:
            genus = _safe_str(row, self.col_genus)
            species = _safe_str(row, self.col_species)
            matches.append(
                {
                    "score": 1.0,
                    "row_index": idx + 2,  # +2 because CSV has header + 1-indexed rows
                    "item_id": _safe_str(row, self.col_item_id),
                    "unique_id": _safe_str(row, self.col_uid),
                    "agent_type": _safe_str(row, self.col_agent_type),
                    "genus": genus,
                    "species": species,
                    "organism": f"{genus} {species}".strip(),
                    "risk_by_source": self._extract_sources(row),
                }
            )

        return {
            "status": "success",
            "query": q,
            "top_k": k,
            "match_count": len(matches),
            "matches": matches,
            "source": str(self.csv_path),
        }


_instance = AbsaRetrieve()
_instance.initiate()
bua_absa_retrieve = _instance.run
