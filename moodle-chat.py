from html.parser import HTMLParser
import http.client
import urllib.parse
import zlib
import sys


class MyHTMLParser(HTMLParser):
    login_token = 0
    session_key = ''
    jsrev = 0
    data_count = 0
    str = ''
    send_mode = False

    def error(self, message):
        pass

    def handle_starttag(self, tag, attrs):
        if not self.send_mode:
            if tag == 'input':
                xx = 0
                login_token_position = -1
                for attr in attrs:
                    xx += 1
                    if login_token_position == xx:
                        self.login_token = attr[1]
                    if attr[1] == 'logintoken':
                        login_token_position = xx + 1

    def handle_data(self, data):
        if self.send_mode:
            if data[:11] == '\n//<![CDATA':
                data = data.split('","')
                try:
                    sesskey = data[1]
                    jsrev = data[5]
                    if sesskey[:7] == 'sesskey':
                        self.session_key = sesskey[10:]
                    if jsrev[:5] == 'jsrev':
                        self.jsrev = jsrev[8:]
                except IndexError:
                    pass
            return
        if self.data_count == 0:
            if data == 'Zeit':
                self.data_count += 1
        elif self.data_count >= 1:
            if data[:10] == 'Sie sind a':
                msg = self.str.split('\n')
                final_msg = []
                tmp_val = 0
                for x in msg:
                    tmp = " ".join(x.split())
                    if tmp_val == 1:
                        tmp_val = 0
                        continue
                    elif tmp[-8:] == 'betreten':
                        print(tmp)
                        tmp_val = 1
                    elif tmp[-9:] == 'verlassen':
                        print(tmp)
                        tmp_val = 1
                    elif tmp != '':
                        final_msg.append(tmp)
                if len(final_msg) == 1:
                    return
                try:
                    if final_msg[0] == 'Keine Mitteilungen gefunden':
                        print(final_msg[0])
                        self.data_count = 0
                        self.str = ''
                        return
                except IndexError:
                    return
                for x in range(0, len(final_msg), 3):
                    print('Message from: ' + final_msg[x])
                    print(final_msg[x + 1])
                    print('Time: ' + final_msg[x + 2] + '\n')
                self.data_count = 0
                self.str = ''
                return
            else:
                self.str = self.str + data
                self.data_count += 1


class MainMenu:
    def __init__(self):
        moodle_chat = MoodleChat()
        while True:
            try:
                choice = input('\n::::: choose an option (h for help): ')
            except KeyboardInterrupt:
                continue
            if choice == 'S':
                moodle_chat.send()
            elif choice == 'R':
                moodle_chat.refresh()
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
        self.parser_for_get = MyHTMLParser()
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

        params = urllib.parse.urlencode({'id': '183'})
        self.conn = http.client.HTTPSConnection('moodle.htwg-konstanz.de')
        self.conn.request('GET', 'https://moodle.htwg-konstanz.de/moodle/mod/chat/gui_basic/index.php?id=183',
                          params, self.payload)
        response = self.conn.getresponse()
        response.read()

    def refresh(self):
        params = urllib.parse.urlencode({'id': '183'})
        self.conn.request('GET', 'https://moodle.htwg-konstanz.de/moodle/mod/chat/gui_basic/index.php?id=183', params,
                          self.payload)
        try:
            response = self.conn.getresponse()
        except http.client.RemoteDisconnected:
            self.conn = http.client.HTTPSConnection('moodle.htwg-konstanz.de')
            self.conn.request('GET', 'https://moodle.htwg-konstanz.de/moodle/mod/chat/gui_basic/index.php?id=183',
                              params,
                              self.payload)
            response = self.conn.getresponse()
        response = response.read()
        response = zlib.decompress(response, 16 + zlib.MAX_WBITS)
        response = response.decode('utf-8')
        self.parser.feed(response)

    def send(self):
        self.parser.send_mode = True
        self.refresh()
        self.parser.send_mode = False
        message = input("Enter Message: ")
        referer = 'https://moodle.htwg-konstanz.de/moodle/mod/chat/gui_basic/index.php?id=183&newonly=0&last=' +\
                  self.parser.jsrev
        params = urllib.parse.urlencode({'message': message, 'id': '183', 'groupid': '0', 'last': self.parser.jsrev,
                                         'sesskey': self.parser.session_key})
        payload = ({'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'de,en;q=0.5',
                    'Connection': 'keep-alive',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'DNT': '1',
                    'Cookie': self.cookie,
                    'Host': 'moodle.htwg-konstanz.de',
                    'Referer': referer,
                    'Upgrade-Insecure-Requests': '1'})
        self.conn.request('POST', 'https://moodle.htwg-konstanz.de/moodle/mod/chat/gui_basic/index.php', params,
                          payload)
        response = self.conn.getresponse()
        response.read()


MainMenu()
