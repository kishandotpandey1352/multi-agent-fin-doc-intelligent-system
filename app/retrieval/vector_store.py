from pathlib import Path
from typing import List, Tuple

import numpy as np

try:
    import faiss  # type: ignore
except ModuleNotFoundError:
    faiss = None


class FaissStore:
    def __init__(self, index_path: Path, dimension: int) -> None:
        self.index_path = index_path
        self.numpy_path = index_path.with_suffix(".npy")
        self.dimension = dimension
        self._use_faiss = faiss is not None
        self.index = self._load_or_create()

    def _load_or_create(self):
        if self._use_faiss:
            if self.index_path.exists():
                index = faiss.read_index(str(self.index_path))
                if index.d != self.dimension:
                    raise ValueError(
                        f"Index dimension mismatch: expected {self.dimension}, found {index.d}"
                    )
                return index

            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            return faiss.IndexFlatIP(self.dimension)

        if self.numpy_path.exists():
            vectors = np.load(self.numpy_path)
            if vectors.ndim != 2 or vectors.shape[1] != self.dimension:
                raise ValueError(
                    f"NumPy index dimension mismatch: expected {self.dimension}, found {vectors.shape}"
                )
            return vectors.astype("float32")

        self.numpy_path.parent.mkdir(parents=True, exist_ok=True)
        return np.zeros((0, self.dimension), dtype="float32")

    def reset(self) -> None:
        if self._use_faiss:
            self.index = faiss.IndexFlatIP(self.dimension)
            return
        self.index = np.zeros((0, self.dimension), dtype="float32")

    def add(self, vectors: np.ndarray) -> Tuple[int, int]:
        if vectors.ndim != 2 or vectors.shape[1] != self.dimension:
            raise ValueError("Embedding array shape does not match index dimension")

        if self._use_faiss:
            start_id = self.index.ntotal
            self.index.add(vectors)
            end_id = self.index.ntotal
            return start_id, end_id

        start_id = self.index.shape[0]
        self.index = np.vstack([self.index, vectors])
        end_id = self.index.shape[0]
        return start_id, end_id

    def search(self, query_vector: np.ndarray, top_k: int) -> Tuple[List[int], List[float]]:
        if query_vector.ndim != 2:
            raise ValueError("Query embedding must have shape (1, dimension)")

        if self._use_faiss:
            scores, ids = self.index.search(query_vector, top_k)
            found_ids = [int(i) for i in ids[0].tolist() if i >= 0]
            found_scores = [float(s) for s in scores[0].tolist()[: len(found_ids)]]
            return found_ids, found_scores

        if self.index.shape[0] == 0:
            return [], []

        sims = self.index @ query_vector[0]
        order = np.argsort(-sims)[:top_k]
        found_ids = [int(i) for i in order.tolist()]
        found_scores = [float(sims[i]) for i in order.tolist()]
        return found_ids, found_scores

    def save(self) -> None:
        if self._use_faiss:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_path))
            return

        self.numpy_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(self.numpy_path, self.index)
