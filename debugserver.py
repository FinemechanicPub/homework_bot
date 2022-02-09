"""Модуль сервера разработчика для отладки бота."""

from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = '127.0.0.1'
PORT = 80
SAMPLE_NO_HOMEWORKS = '''{
   "homeworks":[],
   "current_date":1581604970
}
'''
SAMPLE_MULTIMPLE_HOMEWORKS = '''{
   "homeworks":[
      {
         "id":124,
         "status":"rejected",
         "homework_name":"username__hw_python_oop.zip",
         "reviewer_comment":"Код не по PEP8, нужно исправить",
         "date_updated":"2020-02-13T16:42:47Z",
         "lesson_name":"Итоговый проект"
      },
      {
         "id":123,
         "status":"approved",
         "homework_name":"username__hw_test.zip",
         "reviewer_comment":"Всё нравится",
         "date_updated":"2020-02-11T14:40:57Z",
         "lesson_name":"Тестовый проект"
      }
   ],
   "current_date":1581604970
}
'''


class DebugServer(BaseHTTPRequestHandler):
    """Имитатор сервиса сообщения статуса домашней работы."""

    def do_GET(self):
        """Формирование ответа на запрос."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(SAMPLE_MULTIMPLE_HOMEWORKS, 'utf-8'))


if __name__ == '__main__':
    server = HTTPServer((HOST, PORT), DebugServer)
    print('Server started http://%s:%s' % (HOST, PORT))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    print("Server stopped.")
