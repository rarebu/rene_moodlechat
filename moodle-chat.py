from html.parser import HTMLParser
import http.client
import urllib.parse
import zlib
import sys
import time


class MyHTMLParser(HTMLParser):
    login_token = 0
    session_key = ''
    jsrev = 0

    def error(self, message):
        pass

    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            xx = 0
            login_token_position = -1
            for attr in attrs:
                xx += 1
                if login_token_position == xx:
                    self.login_token = attr[1]  # todo break
                if attr[1] == 'logintoken':
                    login_token_position = xx + 1

    # def handle_endtag(self, tag):
    #     print("End tag  :", tag)

    def handle_data(self, data):
        if data[:11] == '\n//<![CDATA':
            data = data.split('","')
            try:
                sesskey = data[1]
                jsrev = data[5]
                if sesskey[:7] == 'sesskey':
                    self.session_key = sesskey[10:]
                if jsrev[:5] == 'jsrev':
                    self.jsrev = jsrev[8:]  # todo break
            except IndexError:
                pass

    # def handle_comment(self, data):
    #     print("Comment  :", data)

    # def handle_decl(self, data):
    #     print("Decl     :", data)

    def handle_data(self, data):
        if data[:11] == '\n//<![CDATA':
            data = data.split('","')
            try:
                sesskey = data[1]
                jsrev = data[5]
                if sesskey[:7] == 'sesskey':
                    self.session_key = sesskey[10:]
                if jsrev[:5] == 'jsrev':
                    self.jsrev = jsrev[8:]  # todo break
            except IndexError:
                pass

    # def handle_comment(self, data):
    #     print("Comment  :", data)

    # def handle_decl(self, data):
    #     print("Decl     :", data)


class MainMenu:
    def __init__(self):
        moodle_chat = MoodleChat()
        while True:
            try:
                choice = input('\n::::: choose an option (h for help): ')
            except KeyboardInterrupt:
                continue
            if choice == 'R':
                moodle_chat.refresh()
            elif choice == 'S':
                moodle_chat.send()
            elif choice == 'Q':
                print('\n::::: Quitting..')
                break
            else:
                self.print_options()
        sys.exit()

    @staticmethod
    def print_options():
        print('Valid options are R (Refresh), S (Send) and Q (Quit)')


class MoodleChat:
    def __init__(self):
        self.parser = MyHTMLParser()
        self.conn = http.client.HTTPSConnection('moodle.htwg-konstanz.de')

        self.conn.request('GET', '/moodle/login/index.php')
        response = self.conn.getresponse()
        headers = response.getheaders()[2][1]
        cookie = headers.split('; path=')[0]
        self.parser.feed(response.read().decode('utf-8'))
        login_token = self.parser.login_token
        params = urllib.parse.urlencode({'username': 'rnetin', 'password': 'ntsmobil', 'logintoken':
                                         login_token})
        payload = ({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'de,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'DNT': '1',
                    'Cookie': cookie,
                    'Host': 'moodle.htwg-konstanz.de',
                    'Referer': 'moodle.htwg-konstanz.de/moodle/',
                    'Upgrade-Insecure-Requests': '1'})

        self.conn.request('POST', '/moodle/login/index.php', params, payload)
        response = self.conn.getresponse()
        response.read()
        headers = response.getheaders()
        self.cookie = headers[5][1].split(';')[0]
        location = headers[7][1]
        test_session_id = location.split('?testsession=')[1]
        params = urllib.parse.urlencode({'testsession': test_session_id})
        self.payload = ({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                         'Accept-Encoding': 'gzip, deflate, br',
                         'Accept-Language': 'de,en;q=0.5',
                         'Connection': 'keep-alive',
                         'Content-Type': 'application/x-www-form-urlencoded',
                         'DNT': '1',
                         'Cookie': self.cookie,
                         'Host': 'moodle.htwg-konstanz.de',
                         'Referer': 'https://moodle.htwg-konstanz.de/moodle/',
                         'Upgrade-Insecure-Requests': '1'})

        self.conn.request('GET', location, params, self.payload)
        response = self.conn.getresponse()
        response.read()

        self.conn.request('GET', 'https://moodle.htwg-konstanz.de/moodle/', None, self.payload)
        response = self.conn.getresponse()
        response.read()

    def refresh(self):

        params = urllib.parse.urlencode({'id': '183'})
        self.conn.request('GET', 'https://moodle.htwg-konstanz.de/moodle/mod/chat/gui_basic/index.php?id=183', params,
                          self.payload)
        response = self.conn.getresponse()
        response = response.read()
        response = zlib.decompress(response, 16 + zlib.MAX_WBITS)
        print('DATA: ' + str(response))

    def send(self):
        params = urllib.parse.urlencode({'message': 'hey test', 'id': '183', 'groupid': '0', 'last': self.parser.jsrev,
                                         'sesskey': self.parser.session_key})
        payload = ({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'de,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'DNT': '1',
                    'Cookie': self.cookie,
                    'Host': 'moodle.htwg-konstanz.de',
                    'Referer': 'https://moodle.htwg-konstanz.de/moodle/mod/chat/gui_basic/index.php',
                    'Upgrade-Insecure-Requests': '1'})
        self.conn.request('POST', 'https://moodle.htwg-konstanz.de/moodle/mod/chat/gui_basic/index.php', params,
                          payload)
        response = self.conn.getresponse()
        data = response.read()
        data = zlib.decompress(data, 16 + zlib.MAX_WBITS).decode('utf-8')
        headers = response.getheaders()
        print("POST " + str(response.getcode()))
        #print(str(data))
        print(str(headers))
        for x in headers:
            print(x)
        # params = urllib.parse.urlencode({'newonly': '0', 'id': '183', 'last': self.parser.jsrev})
        # self.conn.request('GET', 'https://moodle.htwg-konstanz.de/moodle/mod/chat/gui_basic/index.php', params, payload)
        # response = self.conn.getresponse()
        # data = response.read()
        # data = data.decode('utf-8')
        # headers = response.getheaders()
        # print("GET " + str(response.getcode()))
        # print(str(data))
        # print(str(headers))


MainMenu()
