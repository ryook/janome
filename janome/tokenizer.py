# -*- coding: utf-8 -*-

# Copyright 2015 moco_beta
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
The tokenizer module supplies Token and Tokenizer classes.

Usage:

>>> from janome.tokenizer import Tokenizer
>>> t = Tokenizer()
>>> for token in t.tokenize(u'すもももももももものうち'):
...   print(token)
... 
すもも	名詞,一般,*,*,*,*,すもも,スモモ,スモモ
も	助詞,係助詞,*,*,*,*,も,モ,モ
もも	名詞,一般,*,*,*,*,もも,モモ,モモ
も	助詞,係助詞,*,*,*,*,も,モ,モ
もも	名詞,一般,*,*,*,*,もも,モモ,モモ
の	助詞,連体化,*,*,*,*,の,ノ,ノ
うち	名詞,非自立,副詞可能,*,*,*,うち,ウチ,ウチ

with user dictionary (IPAdic format):

.. code-block:: shell

  $ cat examples/user_ipadic.csv 
  東京スカイツリー,1288,1288,4569,名詞,固有名詞,一般,*,*,*,東京スカイツリー,トウキョウスカイツリー,トウキョウスカイツリー
  東武スカイツリーライン,1288,1288,4700,名詞,固有名詞,一般,*,*,*,東武スカイツリーライン,トウブスカイツリーライン,トウブスカイツリーライン
  とうきょうスカイツリー駅,1288,1288,4143,名詞,固有名詞,一般,*,*,*,とうきょうスカイツリー駅,トウキョウスカイツリーエキ,トウキョウスカイツリーエキ

>>> t = Tokenizer("user_ipadic.csv", udic_enc="utf8")
>>> for token in t.tokenize(u'東京スカイツリーへのお越しは、東武スカイツリーライン「とうきょうスカイツリー駅」が便利です。'):
...  print(token)... 
... 
東京スカイツリー	名詞,固有名詞,一般,*,*,*,東京スカイツリー,トウキョウスカイツリー,トウキョウスカイツリー
へ	助詞,格助詞,一般,*,*,*,へ,ヘ,エ
の	助詞,連体化,*,*,*,*,の,ノ,ノ
お越し	名詞,一般,*,*,*,*,お越し,オコシ,オコシ
は	助詞,係助詞,*,*,*,*,は,ハ,ワ
、	記号,読点,*,*,*,*,、,、,、
東武スカイツリーライン	名詞,固有名詞,一般,*,*,*,東武スカイツリーライン,トウブスカイツリーライン,トウブスカイツリーライン
「	記号,括弧開,*,*,*,*,「,「,「
とうきょうスカイツリー駅	名詞,固有名詞,一般,*,*,*,とうきょうスカイツリー駅,トウキョウスカイツリーエキ,トウキョウスカイツリーエキ
」	記号,括弧閉,*,*,*,*,」,」,」
が	助詞,格助詞,一般,*,*,*,が,ガ,ガ
便利	名詞,形容動詞語幹,*,*,*,*,便利,ベンリ,ベンリ
です	助動詞,*,*,*,特殊・デス,基本形,です,デス,デス
。	記号,句点,*,*,*,*,。,。,。

with user dictionary (simplified format):

.. code-block:: shell

  $ cat examples/user_simpledic.csv 
  東京スカイツリー,カスタム名詞,トウキョウスカイツリー
  東武スカイツリーライン,カスタム名詞,トウブスカイツリーライン
  とうきょうスカイツリー駅,カスタム名詞,トウキョウスカイツリーエキ

>>> t = Tokenizer("user_simpledic.csv", udic_type="simpledic", udic_enc="utf8")
>>> for token in t.tokenize(u'東京スカイツリーへのお越しは、東武スカイツリーライン「とうきょうスカイツリー駅」が便利です。'):
...   print(token)

"""

import sys
import os
from .lattice import Lattice, Node, BOS, EOS, NodeType
from .dic import UserDictionary, CompiledUserDictionary

PY3 = sys.version_info[0] == 3

class Token:
    u"""
    A Token object contains all information for a token.
    """

    def __init__(self, node):
        self.surface = node.surface
        """surface form (表層形)"""
        self.part_of_speech = node.part_of_speech
        """part of speech (品詞)"""
        self.infl_type = node.infl_type
        """terminal form (活用型)"""
        self.infl_form = node.infl_form
        """stem form (活用形)"""
        self.base_form = node.base_form
        """base form (基本形)"""
        self.reading = node.reading
        """"reading (読み)"""
        self.phonetic = node.phonetic
        """pronounce (発音)"""
        self.node_type = node.node_type

    def __str__(self):
        if PY3:
            return '%s\t%s,%s,%s,%s,%s,%s' % \
               (self.surface, self.part_of_speech, self.infl_type, self.infl_form, self.base_form, self.reading, self.phonetic)
        else:
            return '%s\t%s,%s,%s,%s,%s,%s' % \
               (self.surface.encode('utf-8'),
                self.part_of_speech.encode('utf-8'),
                self.infl_type.encode('utf-8'),
                self.infl_form.encode('utf-8'),
                self.base_form.encode('utf-8'),
                self.reading.encode('utf-8'),
                self.phonetic.encode('utf-8'))


class Tokenizer:
    u"""
    A Tokenizer tokenizes Japanese texts with system and optional user defined dictionary.
    It is strongly recommended to re-use a Tokenizer object because object initialization cost is high. 
    """
    MAX_CHUNK_SIZE = 1000
    CHUNK_SIZE = 500

    def __init__(self, udic='', udic_enc='utf8', udic_type='ipadic', max_unknown_length=1024):
        """
        Initialize Tokenizer object with optional arguments.

        :param udic: (Optional) user dictionary file (CSV format) or directory path to compiled dictionary data
        :param udic_enc: (Optional) character encoding for user dictionary. default is 'utf-8'
        :param udic_type: (Optional) user dictionray type. supported types are 'ipadic' and 'simpledic'. default is 'ipadic'
        :param max_unknows_length: (Optional) max unknown word length. default is 1024.

        .. seealso:: See http://mocobeta.github.io/janome/en/#use-with-user-defined-dictionary for details for user dictionary.
        """
        
        from sysdic import SYS_DIC
        self.sys_dic = SYS_DIC
        if udic:
            if udic.endswith('.csv'):
                # build user dictionary from CSV
                self.user_dic = UserDictionary(udic, udic_enc, udic_type, SYS_DIC.connections)
            elif os.path.isdir(udic):
                # load compiled user dictionary
                self.user_dic = CompiledUserDictionary(udic, SYS_DIC.connections)
            else:
                self.user_dic = None
        else:
            self.user_dic = None
        self.max_unknown_length = max_unknown_length

    def tokenize(self, text, stream = False):
        u"""
        Tokenize the text string.

        :param text: unicode string to be tokenized
        :param stream: (Optional) if given True use stream mode. default is False.

        :return: list of tokens (stream = False) or token generator (stream = True)
        """
        if stream:
            return self.__tokenize_stream(text)
        else:
            return list(self.__tokenize_stream(text))

    def __tokenize_stream(self, text):
        text = text.strip()
        text_length = len(text)
        processed = 0
        while processed < text_length:
            tokens, pos = self.__tokenize_partial(text[processed:])
            for token in tokens:
                yield token
            processed += pos


    def __tokenize_partial(self, text):
        chunk_size = min(len(text), Tokenizer.MAX_CHUNK_SIZE)
        lattice = Lattice(chunk_size, self.sys_dic)
        pos = 0
        while not self.__should_split(text, pos):
            # user dictionary
            if self.user_dic:
                entries = self.user_dic.lookup(text[pos:])
                for e in entries:
                    lattice.add(Node(e, NodeType.USER_DICT))
                matched = len(entries) > 0

            # system dictionary
            entries = self.sys_dic.lookup(text[pos:])
            for e in entries:
                lattice.add(Node(e, NodeType.SYS_DICT))
            matched = len(entries) > 0

            # unknown
            cates = self.sys_dic.get_char_categories(text[pos])
            if cates:
                for cate in cates:
                    if matched and not self.sys_dic.unknown_invoked_always(cate):
                        continue
                    # unknown word length
                    length = self.sys_dic.unknown_length(cate) \
                        if not self.sys_dic.unknown_grouping(cate) else self.max_unknown_length
                    assert length >= 0
                    # buffer for unknown word
                    buf = text[pos]
                    for p in range(pos + 1, min(len(text), pos + length + 1)):
                        _cates =  self.sys_dic.get_char_categories(text[p])
                        if cate in _cates or any(cate in _compat_cates for _compat_cates in _cates.values()):
                            buf += text[p]
                        else:
                            break
                    unknown_entries = self.sys_dic.unknowns.get(cate)
                    assert unknown_entries
                    for entry in unknown_entries:
                        left_id, right_id, cost, part_of_speech = entry
                        dummy_dict_entry = (buf, left_id, right_id, cost, part_of_speech, '*', '*', '*', '*', '*')
                        lattice.add(Node(dummy_dict_entry, NodeType.UNKNOWN))

            pos += lattice.forward()
        lattice.end()
        min_cost_path = lattice.backward()
        assert isinstance(min_cost_path[0], BOS)
        assert isinstance(min_cost_path[-1], EOS)
        tokens = [Token(node) for node in min_cost_path[1:-1]]
        return (tokens, pos)

    def __should_split(self, text, pos):
        return \
            pos >= len(text) or \
            pos >= Tokenizer.MAX_CHUNK_SIZE or \
            (pos >= Tokenizer.CHUNK_SIZE and self.__splittable(text[:pos]))

    def __splittable(self, text):
        return self.__is_punct(text[-1]) or self.__is_newline(text)

    def __is_punct(self, c):
        return c == u'、' or c == u'。' or c == u',' or c == u'.' or c == u'？' or c == u'?' or c == u'！' or c == u'!'

    def __is_newline(self, text):
        return text.endswith('\n\n') or text.endswith('\r\n\r\n')