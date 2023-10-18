# coding=utf-8
# Copyright 2018-2023 EvaDB
# ... [rest of your imports and license info]

from evadb.functions.abstract.abstract_function import AbstractFunction
import openai
import pandas as pd
import numpy as np
from evadb.catalog.catalog_type import NdArrayType
from evadb.configuration.configuration_manager import ConfigurationManager
from evadb.functions.abstract.abstract_function import AbstractFunction
from evadb.functions.decorators.decorators import forward, setup
from evadb.functions.decorators.io_descriptors.data_types import PandasDataframe
from evadb.utils.generic_utils import try_to_import_openai

class OpenAIEmbeddingExtractor(AbstractFunction):

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
        embedding_list = openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']

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
            print(row)
            data = row[0]  # Access data using column label
            embedded_list = OpenAIEmbeddingExtractor.get_embedding(data)
            return embedded_list

        ret = pd.DataFrame()
        ret["features"] = df.apply(_forward, axis=1)
        return ret
