#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
from cipin.chineseproofread import proofread
from cipin.checkproof import proofcheck

def main():
    ptarget=proofread()
    ptarget.proofreadAndSuggest("天汽")

if __name__=="__main__":
    print(111111111111111111111)

    main()



