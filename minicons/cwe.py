from typing import Iterable, Union, List, Dict, Optional, Tuple

from .utils import find_pattern, find_index, find_paired_indices

from transformers import AutoModel, AutoTokenizer
import torch

class CWE():
    def __init__(self, model_name: str, device: str = 'cpu') -> None:

        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast = True)
        self.model = AutoModel.from_pretrained(model_name, return_dict = True, output_hidden_states = True)

        self.layers = self.model.config.num_hidden_layers

        if self.tokenizer.pad_token is None:
            self.tokenizer.add_special_tokens({"additional_special_tokens": ["<|pad|>"]})
            self.tokenizer.pad_token = "<|pad|>"
            self.model.resize_token_embeddings(len(self.tokenizer))
        
        self.model.to(self.device)
        self.model.eval()

    def encode_text(self, text: Union[str, List[str]], layer: int = None) -> Tuple:

        sentences = [text] if isinstance(text, str) else text

        # Encode sentence into ids stored in the model's embedding layer(s).
        encoded = self.tokenizer.batch_encode_plus(sentences, padding = 'longest', return_tensors="pt")
        encoded = encoded.to(self.device)

        input_ids = encoded['input_ids']

        # Compute hidden states for the sentence for the given layer.
        output = self.model(**encoded)

#         # Hidden states appear as the last element of the otherwise custom hidden_states object
        if layer != 'all':
            if layer is None:
                layer = self.layers
            elif layer > self.layers:
                raise ValueError(f"Number of layers specified ({layer}) exceed layers in model ({self.layers})!")
            hidden_states = output.hidden_states[layer]
            if "cuda" in self.device:
                input_ids = input_ids.cpu()
                hidden_states = hidden_states.detach().cpu()
            else:
                hidden_states = hidden_states.detach()
        else:
            hidden_states = output.hidden_states
        
            if "cuda" in self.device:
                input_ids = input_ids.cpu()
                hidden_states = [h.detach().cpu() for h in hidden_states]
            else:
                hidden_states = [h.detach() for h in hidden_states]

        return input_ids, hidden_states
    
    # A function that extracts the representation of a given word in a sentence (first occurrence only)

    def extract_representation(self, text, layer:int = None) -> Union[torch.Tensor, List[torch.Tensor]]:
        
        sentences = [text] if isinstance(text[0], str) else text

        num_inputs = len(sentences)

        input_ids, hidden_states = self.encode_text(list(list(zip(*sentences))[0]), layer)

        if isinstance(sentences[0][1], str):
            sentences = [(s, find_index(s, w)) for s, w in sentences]
    
        search_queries = [self.tokenizer.encode_plus(f' {" ".join(s.split()[idx[0]:idx[1]])}', add_special_tokens = False)['input_ids'] for s, idx in sentences]

        query_idx = list(map(lambda x: find_pattern(x[0], x[1]), zip(search_queries, input_ids.tolist())))

        if layer != 'all':
            if layer is None:
                layer = self.layers
            elif layer > self.layers:
                raise ValueError(f"Number of layers specified ({layer}) exceed layers in model ({self.layers})!")
            representations = hidden_states[torch.arange(num_inputs)[:, None], query_idx].mean(1)
        else:
            representations = list(map(lambda x: x[torch.arange(num_inputs)[:, None], query_idx].mean(1), hidden_states))
        
        return representations

    def extract_paired_representations(self, text, layer:int = None) -> Union[torch.Tensor, List[torch.Tensor]]:
        '''
            Given input of the form (<sentence>, <word1>, <word2>) produce paired tensors that represent the words in the sentence, as encoded by the model
        '''
        sentences = [text] if isinstance(text[0], str) else text

        num_inputs = len(sentences)

        input_ids, hidden_states = self.encode_text(list(list(zip(*sentences))[0]), layer)

        if isinstance(sentences[0][1], str):
            sentences = [(s, *find_paired_indices(s, w1, w2)) for s, w1, w2 in sentences]
        
        search_queries1 = [self.tokenizer.encode_plus(f' {" ".join(s.split()[idx1[0]:idx1[1]])}', add_special_tokens = False)['input_ids'] for s, idx1, idx2 in sentences]
        search_queries2 = [self.tokenizer.encode_plus(f' {" ".join(s.split()[idx2[0]:idx2[1]])}', add_special_tokens = False)['input_ids'] for s, idx1, idx2 in sentences]

        query_idx1 = list(map(lambda x: find_pattern(x[0], x[1]), zip(search_queries1, input_ids.tolist())))
        query_idx2 = list(map(lambda x: find_pattern(x[0], x[1]), zip(search_queries2, input_ids.tolist())))

        if layer != 'all':
            if layer is None:
                layer = self.layers
            elif layer > self.layers:
                raise ValueError(f"Number of layers specified ({layer}) exceed layers in model ({self.layers})!")
            representations1 = hidden_states[torch.arange(num_inputs)[:, None], query_idx1].mean(1)
            representations2 = hidden_states[torch.arange(num_inputs)[:, None], query_idx2].mean(1)
        else:
            representations1 = list(map(lambda x: x[torch.arange(num_inputs)[:, None], query_idx1].mean(1), hidden_states))
            representations2 = list(map(lambda x: x[torch.arange(num_inputs)[:, None], query_idx2].mean(1), hidden_states))
        
        return representations1, representations2



    def context_cosine(self, sentence: str, word: str, layer: int = None):

        raise NotImplementedError

    





# ---
# class CWE():
#     def __init__(self, model: str, all_layers: bool = False, device: str = "cpu") -> None:
        
#         self.model = model
#         self.tokenizer = AutoTokenizer.from_pretrained(self.model)
#         # self.vocab = self.tokenizer.vocab

#         self.config = AutoConfig.from_pretrained(self.model, output_hidden_states = all_layers)

#         self.layers = self.config.num_hidden_layers

#         self.transformer = AutoModel.from_config(self.config)
#         self.transformer.to(device)
#         self.transformer.eval()

#     def tokenize(self, sentence: str) -> list:
#         return self.tokenizer.tokenize(sentence)

#     # def encode(self, sentence: list):
#     #     word2ids = self.tokenizer.batch_encode_plus(sentence, pad_to_max_length = True, return_tensors = "pt")
#     #     # if "gpt" in 
#     #     return word2ids
    
#     def encode_sentence(self, sentence: str, layer: int = None):

#         if layer is None:
#             layer = self.layers
#         # Encode sentence into ids stored in the model's embedding layer(s).
#         encoded = self.tokenizer.batch_encode_plus([sentence], return_tensors="pt")
#         input_ids = encoded["input_ids"]

#         # Compute hidden states for the sentence for the given layer.
#         hidden_states = self.transformer(input_ids = input_ids)

#         # Hidden states appear as the last element of the otherwise custom hidden_states object
#         hidden_states = hidden_states[-1][layer]

#         return encoded, hidden_states

#     def context_cosine(self, sentence: str, word: str, layer: int = None):

#         if layer is None:
#             layer = self.layers

#         encoded, hidden_states = self.encode_sentence(sentence, layer)
#         input_ids = encoded['input_ids']

#         word_id = self.tokenizer.encode(word, add_special_tokens = False, add_prefix_space = True)

#         if len(word_id) > 1:
#             raise ValueError("Word not in Transformer's Vocabulary")
#         else:
#             word_id = word_id[0]

#         word_idx = (input_ids == word_id).nonzero().flatten()[1]

#         sentence_idx = list(range(0, input_ids.shape[1]))

#         # only select ids that do not correspond to the word.
#         context_idx = sentence_idx[0:word_idx] + sentence_idx[word_idx + 1:]
#         context_ids = input_ids[0].tolist()[0:word_idx] + input_ids[0].tolist()[word_idx + 1:]

#         context = hidden_states[0, context_idx, :]
#         word_rep = hidden_states[:, word_idx, :]

#         cosines = torch.nn.functional.cosine_similarity(word_rep, context).tolist()

#         tokens = [self.tokenizer.convert_ids_to_tokens(x) for x in context_ids]
#         words = ["".join(self.tokenizer.convert_tokens_to_string(x).split()) for x in tokens]

#         return words, cosines
