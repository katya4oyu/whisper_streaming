#!/usr/bin/env python3
"""
局所合意機能のテスト用スクリプト
"""

import sys
import logging
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from hypothesis_buffer import HypothesisBuffer, HypothesisBufferN

# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_agreement_iterations():
    """局所合意の動作をテスト"""
    
    # 異なる合意回数でテスト
    for iterations in [2, 3, 4]:
        print(f"\n=== 局所合意回数: {iterations} ===")
        
        # 適切なクラスを選択
        if iterations == 2:
            buffer = HypothesisBuffer()
        else:
            buffer = HypothesisBufferN(agreement_iterations=iterations)
        
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
