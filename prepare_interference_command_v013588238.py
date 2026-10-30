"""Print a comparison command for interactive chat.py (does not train)."""
import argparse
from evidence_aware_route_v013588236 import encode_request
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--topic",default="宇宙")
 p.add_argument("--evidence",default="遠方の銀河が遠ざかっているという観測から、宇宙は膨張していると解釈される。")
 a=p.parse_args()
 print("/interference-compare "+encode_request(a.topic,a.evidence).split(" ",1)[1])
if __name__=="__main__":main()
