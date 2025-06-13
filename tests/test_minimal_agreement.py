#!/usr/bin/env python3
"""
局所合意機能の最小テスト（依存関係なし）
"""

import sys
import logging

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class MinimalHypothesisBuffer:
    """テスト用の最小実装"""
    
    def __init__(self, agreement_iterations=2):
        self.commited_in_buffer = []
        self.buffer = []
        self.new = []
        
        # 局所合意の回数を設定（デフォルトは2回）
        self.agreement_iterations = max(2, agreement_iterations)  # 最小2回
        
        # 過去の複数の結果を保持するためのバッファ
        self.history_buffers = []  # [(buffer1, buffer2, ...), ...]

        self.last_commited_time = 0
        self.last_commited_word = None

    def insert(self, new, offset):
        # 簡略化された挿入処理
        new = [(a+offset,b+offset,t) for a,b,t in new]
        self.new = [(a,b,t) for a,b,t in new if a > self.last_commited_time-0.1]

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

    def complete(self):
        return self.buffer

def test_agreement_iterations():
    """局所合意の動作をテスト"""
    
    # 異なる合意回数でテスト
    for iterations in [2, 3, 4]:
        print(f"\n=== 局所合意回数: {iterations} ===")
        
        buffer = MinimalHypothesisBuffer(agreement_iterations=iterations)
        
        # シミュレートされた書き起こし結果
        # 各結果は (start_time, end_time, word) のタプルのリスト
        results = [
            [(0.0, 1.0, "hello"), (1.0, 2.0, "world"), (2.0, 3.0, "test")],
            [(0.0, 1.0, "hello"), (1.0, 2.0, "world"), (2.0, 3.0, "example")],  # 3番目の単語が異なる
            [(0.0, 1.0, "hello"), (1.0, 2.0, "world"), (2.0, 3.0, "example")],  # 一致
            [(0.0, 1.0, "hello"), (1.0, 2.0, "world"), (2.0, 3.0, "example")],  # 一致
            [(0.0, 1.0, "hello"), (1.0, 2.0, "world"), (2.0, 3.0, "example")],  # 一致
        ]
        
        for i, result in enumerate(results):
            print(f"\n--- イテレーション {i+1} ---")
            print(f"入力: {[word for _, _, word in result]}")
            
            buffer.insert(result, 0.0)
            committed = buffer.flush()
            
            if committed:
                committed_words = [word for _, _, word in committed]
                print(f"確定: {committed_words}")
            else:
                print("確定: なし")
                
            # 現在のバッファ状態
            current = buffer.complete()
            if current:
                current_words = [word for _, _, word in current]
                print(f"未確定: {current_words}")
            else:
                print("未確定: なし")

if __name__ == "__main__":
    test_agreement_iterations()
