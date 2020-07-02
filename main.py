#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Author: yudengwu
# @Date  : 2020/6/22
import sys
import pinyin
import jieba
import string
import re

PUNCTUATION_LIST = string.punctuation  # 标点符号!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
PUNCTUATION_LIST += "。，？：；｛｝［］‘“”《》／！％……（）"  # 添加额外标点符号


#统计个单词的词频
def construct_dict(file_path):
    word_freq = {}
    with open(file_path, "r",encoding='utf-8') as f:
        for line in f:
            info = line.split()
            word = info[0]
            frequency = info[1]
            word_freq[word] = frequency

    return word_freq

FILE_PATH = "token_freq_pos%40350k_jieba.txt"
phrase_freq = construct_dict( FILE_PATH ) #得到的是各单词词频,如：{'老师上课': '3', '老师傅': '62', '老师宿儒': '老师上课': '3', '老师傅': '62', }

#构建一个自动更正
"""
为拼写错误的短语创建一个自动更正器，我们使用编辑距离为拼写错误的短语创建一个正确的候选列表
根据是正确短语的可能性对正确候选列表进行排序

以下规则:
如果候选的拼音与拼写错误的短语的拼音完全匹配，我们将候选按第一顺序排列，这意味着他们是最有可能被选中的短语。
否则，如果候选的第一个单词的拼音与拼写错误的短语的第一个单词的拼音匹配，我们就输入第二个顺序的候选者
否则，我们将候选对象按三阶排序
"""
import pinyin

#载入编辑距离的单词列表
#cn_words_dict 用于编辑距离的，从里面选择字来菜如或者替换目标词
def load_cn_words_dict( file_path ):
	cn_words_dict = ""
	with open(file_path, "r",encoding='utf-8') as f:
		for word in f:
			cn_words_dict += word.strip()#去除首尾空格
	return cn_words_dict
cn_words_dict = load_cn_words_dict("cn_dict.txt")#导入单字

#函数计算与中文短语的距离
#cn_words_dict 用于编辑距离的，从里面选择字来菜如或者替换目标词
def edits1(phrase, cn_words_dict):
	"`所有的编辑都是一个编辑远离'短语."
	#phrase = phrase.decode("utf-8")
	splits     = [(phrase[:i], phrase[i:]) for i in range(len(phrase) + 1)]#将单词前后分开
	deletes    = [L + R[1:] for L, R in splits if R]#删除
	transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R)>1]#转换
	replaces   = [L + c + R[1:] for L, R in splits if R for c in cn_words_dict]#替换
	inserts    = [L + c + R for L, R in splits for c in cn_words_dict]#插入
	return set(deletes + transposes + replaces + inserts)
#编辑距离生成的词是否在我们前面得到的{词：词频}列表里，是就返回
def known(phrases):
    return set(phrase for phrase in phrases if phrase in phrase_freq)

#得到错误短语的候选短语
#我们根据候选词的拼音对其重要性进行排序
#如果候选词的拼音与错误词完全匹配，则将候选词进行一级数组
#如果候选词的第一个词的拼音与错误词的第一个词匹配，我们将其按二级数组
#否则我们把候选短语放入第三个数组
def get_candidates(error_phrase):
    candidates_1st_order = []
    candidates_2nd_order = []
    candidates_3nd_order = []
    #pinyin.get，get使用一个简单的get()函数，则可以返回拼音的符号，format="strip"去掉音调， delimiter="/"拼音之间的分隔符

    error_pinyin = pinyin.get(error_phrase, format="strip", delimiter="/")#错误拼音
    error_pinyin=str(error_pinyin)#转换成字符串格式，为后面选择拼音打下基础
    cn_words_dict = load_cn_words_dict("cn_dict.txt")#导入单字
    candidate_phrases = list(edits1(error_phrase, cn_words_dict))#编辑距离生成的候选词组
# 暴力全试一遍.
    for candidate_phrase in candidate_phrases:#遍历编辑距离生成的候选词组
        candidate_pinyin = pinyin.get(candidate_phrase, format="strip", delimiter="/")#候选词拼音
        candidate_pinyin=str(candidate_pinyin)

        if candidate_pinyin == error_pinyin:  # 如果错误词拼音等于候选词拼音,则加入第一选择
           candidates_1st_order.append(candidate_phrase)
        elif candidate_pinyin.split("/")[0] == error_pinyin.split("/")[0]: # 第一个音相同
           candidates_2nd_order.append(candidate_phrase)
        else:
            candidates_3nd_order.append(candidate_phrase)#否则加入第三个
    return candidates_1st_order, candidates_2nd_order, candidates_3nd_order



#自动更正单词
def auto_correct(error_phrase):
    c1_order, c2_order, c3_order = get_candidates(error_phrase)#得到的候选正确词
    # print c1_order, c2_order, c3_order
    value1,value2,value3 = [],[],[]
    if c1_order: # 第一梯队有就算第一梯队,
        for i1 in c1_order:
            if i1 in phrase_freq: # 是词组的话,就选出频率最大的
                value1.append(i1)
        return (max(value1, key=phrase_freq.get))
        #一级候选存在，如果候选词拼音与错误单词完全正确，则返回候选词词频最大的单词
    elif c2_order:
        for i2 in c2_order:
            if i2 in phrase_freq:
                value2.append(i2)
        return (max(value2, key=phrase_freq.get))
        #一级候选不存在，二级候选存在，返回二级候选词频最大的词
    else:
        for i3 in c3_order:
            if i3 in phrase_freq:
                value3.append(i3)
        return(max(value3, key=phrase_freq.get))
        #否则，返回三级候选词频最大的
#


#对于任何一个给定的句子，用结巴做分词，
#割完成后，检查word_freq dict中是否存在剩余的短语，如果不存在，则它是拼写错误的短语
#使用auto_correct函数纠正拼写错误的短语
#输出正确的句子

def auto_correct_sentence(error_sentence, verbose=True):
    jieba_cut = jieba.cut(error_sentence, cut_all=False)
    seg_list = "\t".join(jieba_cut).split("\t")  # 分词
    correct_sentence = ""
    for phrase in seg_list:
        correct_phrase = phrase  # 当前词语
        if phrase not in PUNCTUATION_LIST:  # 去除标点符号
            if phrase not in phrase_freq.keys(): # 不在词表中的进行修改
                correct_phrase = auto_correct(phrase)  # 对当前学习进行修正
                if True:
                    print(phrase, correct_phrase)
        correct_sentence += correct_phrase
    return correct_sentence

def main():
    errsent = '重庆是中国的四大火炉之一，因风景锈丽，是"人间天棠"！'
    print("测试 :")
    correct_sent = auto_correct_sentence(errsent)
    print("原始文本：" + errsent + "\n==>\n" + "修正后的文本:" + correct_sent)


if __name__ == "__main__":
    main()
