import threading
import requests
import time
from queue import Queue
from pprint import pprint
from parsel import Selector

downloadPath = 'D:\Book'
# 下载的页面数量
downloadPage = 2

class ThreadCrawl(threading.Thread):
	def __init__(self, threadName, pageQueue, dataQueue):
		super(ThreadCrawl, self).__init__()
		# 线程名
		self.threadName = threadName
		# 页码队列
		self.pageQueue = pageQueue
		# 数据队列
		self.dataQueue = dataQueue
		# 请求报头
		self.headers = {"User-Agent" : "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0;"}

	def run(self):
		print("启动 " + self.threadName)
		while not CRAWL_EXIT:
			try:
				# 取出一个数字先进先出
				# 可选参数block，默认值为True
				#1. 如果对列为空，block为True的话，不会结束，会进入阻塞状态，直到队列有新的数据
				#2. 如果队列为空，block为False的话，就弹出一个Queue.empty()异常，
				page = self.pageQueue.get(False)
				url = 'http://www.txt53.com/html/dushi/list_35_{}.html'.format(str(page))
				print(url)
				content = requests.get(url, headers = self.headers).text
				time.sleep(1)
				self.dataQueue.put(content)
			except:
				pass
		print("结束 " + self.threadName)


class ThreadParse(threading.Thread):
	def __init__(self, threadName, dataQueue):
		super(ThreadParse, self).__init__()
		# 线程名
		self.threadName = threadName
		# 数据队列
		self.dataQueue = dataQueue

	def run(self):
		print("启动 " + self.threadName)
		while not PARSE_EXIT:
			try:
				html = self.dataQueue.get(False)
				self.paser(html)
			except:
				pass
		print("退出" + self.threadName)

	def paser(self, html):
		# 解析html
		sel = Selector(text=html)
		book_url_list = sel.xpath('//div[@class="xiashu"]/ul/li[5]/a/@href').extract()
		book_name_list = sel.xpath('//div[@class="xiashu"]/ul/li[5]/a/text()').extract()
		bookName_url = dict()
		for i in range(len(book_name_list)):
			# book name split example 《从王子到神豪》TXT下载 => 从王子到神豪
			book_name = book_name_list[i].split('《')[1].split('》')[0]
			bookName_url[book_name] = book_url_list[i]
		
		for key in bookName_url.keys():
			download_url = get_book_url(bookName_url[key])
			bookName_url[key] = download_url
		for i in bookName_url:
			print(i, bookName_url[i])
		#download book
		get_download_url(bookName_url)

CRAWL_EXIT = False
PARSE_EXIT = False

def main():
	# 页码的队列，表示20个页面
	pageQueue = Queue(downloadPage)
	# 放入页码的数字，先进先出
	for i in range(1, downloadPage + 1):
		pageQueue.put(i)

	# 采集结果(每页的HTML源码)的数据队列，参数为空表示不限制
	dataQueue = Queue()

	# 三个采集线程的名字
	crawlList = ['采集线程1号', '采集线程2号', '采集线程3号']
	# 存储三个采集线程的列表集合

	threadcrawl = []
	for threadName in crawlList:
		thread = ThreadCrawl(threadName, pageQueue, dataQueue)
		thread.start()
		threadcrawl.append(thread)

	# 三个解析线程的名字
	parseList = ["解析线程1号","解析线程2号","解析线程3号"]
	# 存储三个解析线程
	threadparse = []
	for threadName in parseList:
		thread = ThreadParse(threadName, dataQueue)
		thread.start()
		threadparse.append(thread)

	# 等待pageQueue队列为空，也就是等待之前的操作执行完毕
	while not pageQueue.empty():
		pass

	# 如果pageQueue为空，采集线程退出循环
	global CRAWL_EXIT
	CRAWL_EXIT = True

	print("pageQueue为空")

	for thread in threadcrawl:
		thread.join()
		print("1")

	while not dataQueue.empty():
		pass

	global PARSE_EXIT
	PARSE_EXIT = True

	for thread in threadparse:
		thread.join()
		print("2")

def get_url(page):
	url = 'http://www.txt53.com/html/dushi/list_35_{}.html'.format(str(page))
	response = requests.get(url).text
	sel = Selector(text=response)
	book_url_list = sel.xpath('//div[@class="xiashu"]/ul/li[5]/a/@href').extract()
	book_name_list = sel.xpath('//div[@class="xiashu"]/ul/li[5]/a/text()').extract()
	bookName_url = dict()
	for i in range(len(book_name_list)):
		# book name split example 《从王子到神豪》TXT下载 => 从王子到神豪
		book_name = book_name_list[i].split('《')[1].split('》')[0]
		bookName_url[book_name] = book_url_list[i]
	
	for key in bookName_url.keys():
		download_url = get_book_url(bookName_url[key])
		bookName_url[key] = download_url
	#download book
	get_download_url(bookName_url)

def get_book_url(book_url):
	response = requests.get(book_url).text
	sel = Selector(text=response)
	download_url = sel.xpath('//div[@class="downbox"]/a[1]/@href').extract_first()
	download_txt_url = get_download_book_txt_url(download_url)
	return download_txt_url

#download book
def get_download_book_txt_url(download_url):
	response = requests.get(download_url).text
	sel = Selector(text=response)
	return sel.xpath('//div[@class="shuji"]/ul/li[2]/a/@href').extract_first()
	 

def get_download_url(down_name_url):
	for key in down_name_url.keys():
		r = requests.get(down_name_url[key], stream=True)
		r.raw
		r.raw.read(10)
		with open(downloadPath + '\\{}.txt'.format(key), 'wb') as fd:
			for chunk in r.iter_content(chunk_size=512):
				fd.write(chunk)

def while_page(page):
	for i in range(1, page):
		get_url(i)

if __name__ == '__main__':
	#while_page(downloadPage)
	main()

