# coding=utf-8
# Copyright 2018-2023 EvaDB
# ... [rest of your imports and license info]

from evadb.functions.abstract.abstract_function import AbstractFunction
import openai
import os
import pandas as pd
import numpy as np
import json
from evadb.catalog.catalog_type import NdArrayType
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe
from evadb.utils.generic_utils import try_to_import_openai


class OpenAIEmbeddingExtractor(AbstractFunction):

    def __init__(self):
        self.cache_dir = 'embedding_cache'
        os.makedirs(self.cache_dir, exist_ok=True)

    def cache_embedding_exists(self, text):
        """Check if the embedding cache exists for a given text."""
        cache_file = os.path.join(
            self.cache_dir, f'{self.hash_text(text)}.json')
        return os.path.exists(cache_file)

    def read_cached_embedding(self, text):
        """Read and return the cached embedding."""
        with open(os.path.join(self.cache_dir, f'{self.hash_text(text)}.json'), 'r') as file:
            return json.load(file)

    def cache_embedding(self, text, embedding):
        """Cache the embedding."""
        with open(os.path.join(self.cache_dir, f'{self.hash_text(text)}.json'), 'w') as file:
            json.dump(embedding, file)

    @staticmethod
    def hash_text(text):
        """Create a simple hash of the text for filename."""
        return abs(hash(text)) % (10 ** 8)  # Simple hash function

    @setup(cacheable=True, function_type="chat-completion", batchable=True)
    def setup(
        self,
        model="text-embedding-ada-002",
    ) -> None:
        self.model = model

    @property
    def name(self) -> str:
        return "OpenAIEmbeddingExtractor"

    @staticmethod
    def get_embedding(text, model="text-embedding-ada-002"):
        text = text.replace("\n", " ")

        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        embedding_list = client.embeddings.create(
            input=[text], model=model).data[0].embedding

        # Convert the list to a NumPy array
        return np.array(embedding_list)

    @forward(
        input_signatures=[
            PandasDataframe(
                columns=["data"],
                column_types=[NdArrayType.STR],
                column_shapes=[(1)]
            )
        ],
        output_signatures=[
            PandasDataframe(
                columns=["features"],
                column_types=[NdArrayType.FLOAT32],
                # The shape might change based on OpenAI's output. Adjust accordingly.
                column_shapes=[(1, 1536)]
            )
        ]
    )
    def forward(self, df: pd.DataFrame) -> pd.DataFrame:
        def _forward(row: pd.Series) -> np.ndarray:
            data = row[0]  # Access data using column label

            # Check cache first
            if self.cache_embedding_exists(data):
                return np.array(self.read_cached_embedding(data))

            # If not in cache, fetch and cache embedding
            embedded_list = OpenAIEmbeddingExtractor.get_embedding(data)
            self.cache_embedding(data, embedded_list.tolist())

            return embedded_list

        ret = pd.DataFrame()
        ret["features"] = df.apply(_forward, axis=1)
        return ret
