from unittest import main, mock, TestCase

import homework

SAMPLE_NO_HOMEWORKS = '''{
   "current_date":1581604970
}
'''
SAMPLE_EMPTY_HOMEWORKS = '''{
   "homeworks":[],
   "current_date":1581604970
}
'''
SAMPLE_HOMEWORK = '''{
   "homeworks":[
      {
         "id":124,
         "status":"rejected",
         "homework_name":"username__hw_python_oop.zip",
         "reviewer_comment":"Код не по PEP8, нужно исправить",
         "date_updated":"2020-02-13T16:42:47Z",
         "lesson_name":"Итоговый проект"
      }
   ],
   "current_date":1581604970
}
'''
SAMPLE_HOMEWORK_WRONG_STATUS = '''{
   "homeworks":[
      {
         "id":124,
         "status":"undefined status",
         "homework_name":"username__hw_python_oop.zip",
         "reviewer_comment":"Код не по PEP8, нужно исправить",
         "date_updated":"2020-02-13T16:42:47Z",
         "lesson_name":"Итоговый проект"
      }
   ],
   "current_date":1581604970
}
'''

SAMPLE_HOMEWORK_ILL_FORMED = '''{
   "homeworks":[
      {
         "id":124,
         "reviewer_comment":"Код не по PEP8, нужно исправить",
         "date_updated":"2020-02-13T16:42:47Z",
         "lesson_name":"Итоговый проект"
      }
   ],
   "current_date":1581604970
}
'''

INCORRECT_JSON = '''{
   homeworks":
      {
         "id":124,
         "reviewer_comment":"Код не по PEP8, нужно исправить",
         "date_updated":"2020-02-13T16:42:47Z",
         "lesson_name":"Итоговый проект"
      }
   ],
   "current_date":1581604970
}
'''


class TestRequest(TestCase):
    """Проверка обработки ошибок при запросе."""

    def setUp(self):
        pass

    def test_request_error(self):
        cases = [
            ('http://0.0.0.0', ConnectionError),
            ('http://unknown_address.yandex.ru', ValueError)
        ]
        for url, error in cases:
            with mock.patch('homework.ENDPOINT', url):
                self.assertRaises(
                    error, homework.get_api_answer, current_timestamp=0
                )

    # @mock.patch('requests.get')
    # def test_request_json(self, requests_get):
    #     cases = ['{ homework": [] }']
    #     response = mock.Mock()
    #     for json in cases:
    #         response.json = mock.Mock(return_value=json)
    #         response.status_code = 200
    #         requests_get.return_value = response
    #         self.assertRaises(
    #             homework.JSONDecodeError,
    #             homework.get_api_answer,
    #             current_timestamp=0
    #         )

    def test_check_response(self):
        cases = [
            ([], TypeError),
            ({"current_date": 1581604970}, KeyError),
            ({"homeworks": {"name": "some_name"}}, TypeError),
            ({"homeworks": []}, None)
        ]
        for json_data, error in cases:
            if error:
                self.assertRaises(
                    error, homework.check_response, response=json_data
                )

    def test_parse_status(self):
        pass


if __name__ == '__main__':
    main()
