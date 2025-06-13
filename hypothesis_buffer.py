"""
Hypothesis buffer implementations for local agreement functionality.

This module provides two implementations:
- HypothesisBuffer: Optimized for n=2 iterations (original algorithm)
- HypothesisBufferN: General implementation for n>2 iterations
"""

import sys
import logging

logger = logging.getLogger(__name__)


class HypothesisBuffer:
    """
    Original optimized implementation for local agreement with exactly 2 iterations.
    This maintains the original algorithm for optimal performance in the default case.
    """

    def __init__(self, logfile=sys.stderr):
        self.commited_in_buffer = []
        self.buffer = []
        self.new = []

        self.last_commited_time = 0
        self.last_commited_word = None

        self.logfile = logfile

    def insert(self, new, offset):
        # compare self.commited_in_buffer and new. It inserts only the words in new that extend the commited_in_buffer, it means they are roughly behind last_commited_time and new in content
        # the new tail is added to self.new
        
        new = [(a+offset,b+offset,t) for a,b,t in new]
        self.new = [(a,b,t) for a,b,t in new if a > self.last_commited_time-0.1]

        if len(self.new) >= 1:
            a,b,t = self.new[0]
            if abs(a - self.last_commited_time) < 1:
                if self.commited_in_buffer:
                    # it's going to search for 1, 2, ..., 5 consecutive words (n-grams) that are identical in commited and new. If they are, they're dropped.
                    cn = len(self.commited_in_buffer)
                    nn = len(self.new)
                    for i in range(1,min(min(cn,nn),5)+1):  # 5 is the maximum 
                        c = " ".join([self.commited_in_buffer[-j][2] for j in range(1,i+1)][::-1])
                        tail = " ".join(self.new[j-1][2] for j in range(1,i+1))
                        if c == tail:
                            words = []
                            for j in range(i):
                                words.append(repr(self.new.pop(0)))
                            words_msg = " ".join(words)
                            logger.debug(f"removing last {i} words: {words_msg}")
                            break

    def flush(self):
        """
        Original flush implementation optimized for 2-iteration local agreement.
        Returns committed chunk = the longest common prefix of last 2 inserts.
        """
        # returns committed chunk = the longest common prefix of 2 last inserts.

        commit = []
        while len(self.new) > 0 and len(self.buffer) > 0:

            if self.new[0][2] == self.buffer[0][2]:
                na, nb, nt = self.new.pop(0)
                self.buffer.pop(0)
                commit.append((na, nb, nt))
                self.last_commited_word = nt
                self.last_commited_time = nb
            else:
                break
        self.buffer = self.new
        self.new = []
        self.commited_in_buffer.extend(commit)
        return commit

    def pop_commited(self, time):
        while self.commited_in_buffer and self.commited_in_buffer[0][1] <= time:
            self.commited_in_buffer.pop(0)

    def complete(self):
        return self.buffer


class HypothesisBufferN:
    """
    Extended implementation for local agreement with configurable iterations (n>2).
    Uses history-based tracking to support arbitrary number of agreement iterations.
    """

    def __init__(self, logfile=sys.stderr, agreement_iterations=3):
        self.commited_in_buffer = []
        self.buffer = []
        self.new = []
        
        # 局所合意の回数を設定（最小3回）
        self.agreement_iterations = max(3, agreement_iterations)
        
        # 過去の複数の結果を保持するためのバッファ
        self.history_buffers = []  # [(buffer1, buffer2, ...), ...]

        self.last_commited_time = 0
        self.last_commited_word = None

        self.logfile = logfile

    def insert(self, new, offset):
        # compare self.commited_in_buffer and new. It inserts only the words in new that extend the commited_in_buffer, it means they are roughly behind last_commited_time and new in content
        # the new tail is added to self.new
        
        new = [(a+offset,b+offset,t) for a,b,t in new]
        self.new = [(a,b,t) for a,b,t in new if a > self.last_commited_time-0.1]

        if len(self.new) >= 1:
            a,b,t = self.new[0]
            if abs(a - self.last_commited_time) < 1:
                if self.commited_in_buffer:
                    # it's going to search for 1, 2, ..., 5 consecutive words (n-grams) that are identical in commited and new. If they are, they're dropped.
                    cn = len(self.commited_in_buffer)
                    nn = len(self.new)
                    for i in range(1,min(min(cn,nn),5)+1):  # 5 is the maximum 
                        c = " ".join([self.commited_in_buffer[-j][2] for j in range(1,i+1)][::-1])
                        tail = " ".join(self.new[j-1][2] for j in range(1,i+1))
                        if c == tail:
                            words = []
                            for j in range(i):
                                words.append(repr(self.new.pop(0)))
                            words_msg = " ".join(words)
                            logger.debug(f"removing last {i} words: {words_msg}")
                            break

    def flush(self):
        """
        Extended flush implementation for n-iteration local agreement.
        Returns committed chunk = the longest common prefix of agreement_iterations last inserts.
        """
        # 新しい結果をhistory_buffersに追加
        self.history_buffers.append(self.new[:])  # コピーを追加
        
        # 指定された回数以上の履歴を保持
        if len(self.history_buffers) > self.agreement_iterations:
            self.history_buffers.pop(0)
        
        commit = []
        
        # 指定された回数分の合意が得られていない場合は、current bufferのみ更新
        if len(self.history_buffers) < self.agreement_iterations:
            self.buffer = self.new
            self.new = []
            return commit
        
        # agreement_iterations個のバッファ間で共通プレフィックスを見つける
        min_length = min(len(buf) for buf in self.history_buffers) if self.history_buffers else 0
        
        for i in range(min_length):
            # i番目の位置で全てのバッファが同じ単語を持っているかチェック
            words = [buf[i][2] for buf in self.history_buffers]  # 全バッファのi番目の単語
            
            if len(set(words)) == 1:  # 全て同じ単語
                # 最新の結果からタイムスタンプを取得
                na, nb, nt = self.history_buffers[-1][i]
                commit.append((na, nb, nt))
                self.last_commited_word = nt
                self.last_commited_time = nb
            else:
                break
        
        # commitされた分を各履歴バッファから削除
        for j in range(len(self.history_buffers)):
            self.history_buffers[j] = self.history_buffers[j][len(commit):]
        
        self.buffer = self.new[len(commit):]
        self.new = []
        self.commited_in_buffer.extend(commit)
        
        if commit:
            logger.debug(f"Committed {len(commit)} words after {self.agreement_iterations} iterations agreement")
        
        return commit

    def pop_commited(self, time):
        while self.commited_in_buffer and self.commited_in_buffer[0][1] <= time:
            self.commited_in_buffer.pop(0)

        self.logfile = logfile

    def insert(self, new, offset):
        # compare self.commited_in_buffer and new. It inserts only the words in new that extend the commited_in_buffer, it means they are roughly behind last_commited_time and new in content
        # the new tail is added to self.new
        
        new = [(a+offset,b+offset,t) for a,b,t in new]
        self.new = [(a,b,t) for a,b,t in new if a > self.last_commited_time-0.1]

        if len(self.new) >= 1:
            a,b,t = self.new[0]
            if abs(a - self.last_commited_time) < 1:
                if self.commited_in_buffer:
                    # it's going to search for 1, 2, ..., 5 consecutive words (n-grams) that are identical in commited and new. If they are, they're dropped.
                    cn = len(self.commited_in_buffer)
                    nn = len(self.new)
                    for i in range(1,min(min(cn,nn),5)+1):  # 5 is the maximum 
                        c = " ".join([self.commited_in_buffer[-j][2] for j in range(1,i+1)][::-1])
                        tail = " ".join(self.new[j-1][2] for j in range(1,i+1))
                        if c == tail:
                            words = []
                            for j in range(i):
                                words.append(repr(self.new.pop(0)))
                            words_msg = " ".join(words)
                            logger.debug(f"removing last {i} words: {words_msg}")
                            break

    def flush(self):
        # returns commited chunk = the longest common prefix of the last two hypothesis (self.buffer and self.new).

        commit = []
        while self.new:
            na, nb, nt = self.new[0]

            if len(self.buffer) == 0:
                break

            if self.buffer[0][2] == nt and abs(self.buffer[0][0] - na) < 1:
                commit.append((na, nb, nt))
                self.last_commited_word = nt
                self.last_commited_time = nb
                self.buffer.pop(0)
                self.new.pop(0)
            else:
                break
        self.buffer = self.new
        self.new = []
        self.commited_in_buffer.extend(commit)
        return commit

    def pop_commited(self, time):
        while self.commited_in_buffer and self.commited_in_buffer[0][1] <= time:
            self.commited_in_buffer.pop(0)

    def complete(self):
        return self.buffer


class HypothesisBufferN:
    """
    Extended HypothesisBuffer implementation for n>2 local agreement iterations.
    Uses a history-based approach to track multiple iterations for agreement.
    """

    def __init__(self, agreement_iterations=3, logfile=sys.stderr):
        self.commited_in_buffer = []
        self.buffer = []
        self.new = []
        
        # 局所合意の回数を設定（n>2の場合に使用）
        self.agreement_iterations = max(3, agreement_iterations)  # 最小3回（この実装はn>2用）
        
        # 過去の複数の結果を保持するためのバッファ
        self.history_buffers = []  # [(buffer1, buffer2, ...), ...]

        self.last_commited_time = 0
        self.last_commited_word = None

        self.logfile = logfile

    def insert(self, new, offset):
        # compare self.commited_in_buffer and new. It inserts only the words in new that extend the commited_in_buffer, it means they are roughly behind last_commited_time and new in content
        # the new tail is added to self.new
        
        new = [(a+offset,b+offset,t) for a,b,t in new]
        self.new = [(a,b,t) for a,b,t in new if a > self.last_commited_time-0.1]

        if len(self.new) >= 1:
            a,b,t = self.new[0]
            if abs(a - self.last_commited_time) < 1:
                if self.commited_in_buffer:
                    # it's going to search for 1, 2, ..., 5 consecutive words (n-grams) that are identical in commited and new. If they are, they're dropped.
                    cn = len(self.commited_in_buffer)
                    nn = len(self.new)
                    for i in range(1,min(min(cn,nn),5)+1):  # 5 is the maximum 
                        c = " ".join([self.commited_in_buffer[-j][2] for j in range(1,i+1)][::-1])
                        tail = " ".join(self.new[j-1][2] for j in range(1,i+1))
                        if c == tail:
                            words = []
                            for j in range(i):
                                words.append(repr(self.new.pop(0)))
                            words_msg = " ".join(words)
                            logger.debug(f"removing last {i} words: {words_msg}")
                            break

    def flush(self):
        # returns commited chunk = the longest common prefix of agreement_iterations last inserts.
        
        # 新しい結果をhistory_buffersに追加
        self.history_buffers.append(self.new[:])  # コピーを追加
        
        # 指定された回数以上の履歴を保持
        if len(self.history_buffers) > self.agreement_iterations:
            self.history_buffers.pop(0)
        
        commit = []
        
        # 指定された回数分の合意が得られていない場合は、current bufferのみ更新
        if len(self.history_buffers) < self.agreement_iterations:
            self.buffer = self.new
            self.new = []
            return commit
        
        # agreement_iterations個のバッファ間で共通プレフィックスを見つける
        min_length = min(len(buf) for buf in self.history_buffers) if self.history_buffers else 0
        
        for i in range(min_length):
            # i番目の位置で全てのバッファが同じ単語を持っているかチェック
            words = [buf[i][2] for buf in self.history_buffers]  # 全バッファのi番目の単語
            
            if len(set(words)) == 1:  # 全て同じ単語
                # 最新の結果からタイムスタンプを取得
                na, nb, nt = self.history_buffers[-1][i]
                commit.append((na, nb, nt))
                self.last_commited_word = nt
                self.last_commited_time = nb
            else:
                break
        
        # commitされた分を各履歴バッファから削除
        for j in range(len(self.history_buffers)):
            self.history_buffers[j] = self.history_buffers[j][len(commit):]
        
        self.buffer = self.new[len(commit):]
        self.new = []
        self.commited_in_buffer.extend(commit)
        
        if commit:
            logger.debug(f"Committed {len(commit)} words after {self.agreement_iterations} iterations agreement")
        
        return commit

    def pop_commited(self, time):
        while self.commited_in_buffer and self.commited_in_buffer[0][1] <= time:
            self.commited_in_buffer.pop(0)

    def complete(self):
        return self.buffer
