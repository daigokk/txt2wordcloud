# Special thanks!
# - https://github.com/Sak1361/word_count/blob/master/count_word.py

import MeCab
import re
import urllib.request
import codecs   #unicodeError対策
import random
import time
import argparse
import json
import os
import mojimoji
import japanize_matplotlib
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from wordcloud import WordCloud

class Txt2wordcloud():
    def __init__(self):
        self.s = 0
        self.e = 200000
        self.stops = 2000000
        self.tagger = MeCab.Tagger("-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd")

    def re_def(self, filepath):
        with codecs.open(filepath, 'r', encoding='utf-8', errors='ignore')as f:
        #with open(filepass, 'r')as f:
            l = ""
            re_half = re.compile(r'[!-~]')  # 半角記号,数字,英字
            re_full = re.compile(r'[︰-＠]')  # 全角記号
            re_full2 = re.compile(r'[、・’〜：＜＞＿｜「」｛｝【】『』〈〉“”◯○〔〕…――――◇]')  # 全角で取り除けなかったやつ
            re_comma = re.compile(r'[。]')  # 読点のみ
            re_url = re.compile(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-…]+')
            re_tag = re.compile(r"<[^>]*?>")    #HTMLタグ
            re_n = re.compile(r'\n')  # 改行文字
            re_space = re.compile(r'[\s+]')  #１以上の空白文字
            re_num = re.compile(r"[0-9]")
            start_time = time.time()
            for line in f:
                if re_num.match(line):
                    line = mojimoji.han_to_zen(line, ascii=False)
                line = re_half.sub("", line)
                line = re_full.sub("", line)
                line = re_url.sub("", line)
                line = re_tag.sub("",line)
                line = re_n.sub("", line)
                line = re_space.sub("", line)
                line = re_full2.sub(" ", line)
                line = re_comma.sub("\n",line)  #読点で改行しておく
                l += line
        end_time = time.time() - start_time
        print("無駄処理時間",end_time)
        return l

    def sloth_words(self):    #slothwordのlist化
        if os.path.exists("sloth_words.txt"):
            text = ""
            with open("sloth_words.txt",'r') as f:
                for l in f:
                    text += l
            soup = json.loads(text,encoding='utf-8')
            return soup
        ###sloth_words###
        sloth = 'http://svn.sourceforge.jp/svnroot/slothlib/CSharp/Version1/SlothLib/NLP/Filter/StopWord/word/Japanese.txt'
        slothl_file = urllib.request.urlopen(sloth)
        soup = BeautifulSoup(slothl_file, 'html.parser')
        soup = str(soup).split()
        ###sloth_singleword###
        sloth_1 = 'http://svn.sourceforge.jp/svnroot/slothlib/CSharp/Version1/SlothLib/NLP/Filter/StopWord/word/OneLetterJp.txt'
        slothl_file2 = urllib.request.urlopen(sloth_1)
        soup2 = BeautifulSoup(slothl_file2, 'html.parser')
        soup2 = str(soup2).split()
        soup.extend(soup2)  #1つにまとめる
        ###毎回呼ぶの面倒だからファイル作る
        with open("sloth_words.txt","w") as f:
            text_dic = json.dumps(soup,ensure_ascii=False, indent=2 )
            f.write(text_dic)
        return soup

    def morphologial(self, all_words):
        wakati_data = []
        while True:
            w = all_words[self.s:self.e]
            wakati_data.extend(self.tagger.parse(w).split("\n"))
            if self.e > self.stops or self.e > len(all_words):
                break
            self.s = self.e
            self.e += 200000
        return wakati_data

    def counting(self,all_words):
        stime = time.time()
        dicts = {}  # 単語をカウントする辞書
        print("総文字数:{0}\t({1}万字)".format(len(all_words),len(all_words)/10000))
        mem = 0 #一定単語以上か判別
        #re_hiragana = re.compile(r'[あ-んア-ン一-鿐].')    #ひらがな2文字以上にヒットする正規表現
        sloths = self.sloth_words() #slothのlist
        if len(all_words) > 2000000:
            mem = 1
        while True:
            word_list = []
            wakati = self.morphologial(all_words) #分かち書きアンド形態素解析
            for addlist in wakati:
                addlist = re.split('[\t,]', addlist)  # 空白と","で分割
                if addlist == [] or addlist[0] == 'EOS' or addlist[0] == '' or addlist[0] == 'ー' or addlist[0] == '*':
                    pass
                elif addlist[1] == '名詞':  #名詞のみカウント
                    if addlist[2] == '一般' or addlist[2] == '固有名詞' :#and not addlist[3] == '人名':
                        #print(addlist)  #6番目に未然形とか連用タ接続
                        word_list.append(addlist)  #listごとに区切るのでappendで。extendだとつながる
                else:
                    pass

            for count in word_list:
                
                if count[0] not in dicts:
                    dicts.setdefault(count[0], 1)
                else:
                    dicts[count[0]] += 1
            ###文字数オーバー時###
            if mem:
                if len(all_words) < self.stops:
                    del wakati, addlist, word_list
                    break
                else:
                    del addlist
                    print("{}万字まで終わったよ".format(self.stops/10000))
                    self.stops += 2000000
                    self.s = self.e
                    self.e += 200000
            else:
                break
        for key in list(dicts): #ストップワード除去
            if key in sloths:
                del dicts[key]
        
        dicts_sorted = {}
        for k, v in sorted(dicts.items(), key=lambda x: x[1], reverse=True):  # 辞書を降順に入れる
            dicts_sorted.update( {str(k):int(v)} )
        etime = time.time() - stime
        print("解析処理時間",etime)
        return dicts_sorted

    def plot(self, countedwords, showing_words=20):
        counts = {}
        total = sum(countedwords.values())
        c = 1
        for k, v in sorted(countedwords.items(), key=lambda x: x[1], reverse=True):  # 辞書を降順に入れる
            counts.update( {str(k):int(v)} )
            c += 1
            if c > showing_words:
               break
        fig, ax = plt.subplots(figsize=(6,8))
        ax.barh(range(len(counts)), list(counts.values()), align='center')
        ax.set_title(f'Best {showing_words} in {len(countedwords)} noun words')
        ax.invert_yaxis()
        ax.set_yticks(range(len(counts))) 
        ax.set_yticklabels(counts.keys())#([word[:3] for word in counts.keys()])
        ax.set_xlabel('出現回数')
        for x, y in zip(range(len(counts)), counts.values()):
            ax.text(y+len(counts)*0.1, x, y, ha='center', va='center') #出現回数
            ax.text(y/2, x, f'{(y/total*100):.1f}%', ha='center', va='center', color='white')  #パーセンテージ
        
        fig.tight_layout()
        fig.savefig('barchart.png', dpi=600)
    
    def wordcloud(self, countedwords):
        ws_show = []
        for key, value in countedwords.items():
            if value > 0:
                for j in range(value):
                    ws_show.append(key)
        random.shuffle(ws_show)
        texts = ' '.join(ws_show)
        wordcloud = WordCloud(font_path = '/usr/lib/x86_64-linux-gnu/mecab/dic/fonts-japanese-mincho.ttf',
                            background_color="white",
                            max_words=100,
                            regexp=r"[\w']+",
                            width=640,height=480).generate(texts)
        fig, ax = plt.subplots(figsize=(10,5))
        ax.imshow(wordcloud)
        ax.axis("off")
        fig.savefig("wordcloud.png")
