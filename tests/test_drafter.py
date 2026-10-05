import unittest

from email_drafter import (draft, list_scenarios, render, required_fields,
                           TEMPLATES)


class TestRender(unittest.TestCase):
    def test_zh_render_fills_values(self):
        body = render("leave", {
            "recipient": "李经理", "sender": "张三", "reason": "家中有事",
            "start_date": "10-10", "end_date": "10-12", "days": "3",
            "colleague": "王五", "contact": "微信",
        })
        self.assertIn("李经理", body)
        self.assertIn("10-10 至 10-12", body)
        self.assertIn("张三", body)

    def test_en_render(self):
        body = render("thank_you", {
            "recipient": "Alex", "sender": "Zhang",
            "occasion": "the interview", "detail": "your feedback",
        }, lang="en")
        self.assertIn("Dear Alex", body)
        self.assertIn("the interview", body)

    def test_missing_field_left_as_placeholder(self):
        body = render("job_application", {"sender": "张三"})
        self.assertIn("张三", body)
        # 缺失字段保留 <...> 便于人工补全
        self.assertIn("<recipient>", body)

    def test_unknown_scenario_raises(self):
        with self.assertRaises(KeyError):
            render("not_exist", {})

    def test_invalid_lang_raises(self):
        with self.assertRaises(ValueError):
            render("leave", {}, lang="fr")


class TestMeta(unittest.TestCase):
    def test_list_scenarios(self):
        sc = list_scenarios()
        self.assertIn("job_application", sc)
        self.assertIn("follow_up", sc)
        self.assertEqual(len(sc), len(TEMPLATES))

    def test_required_fields_match_template(self):
        for scene in TEMPLATES:
            fields = required_fields(scene, "zh")
            # sender 通常出现在所有模板里
            self.assertIn("sender", fields)

    def test_draft_no_llm_returns_template(self):
        body = draft("follow_up", {
            "recipient": "王总", "sender": "我", "topic": "合同",
            "status": "已初稿", "deadline": "周五",
        }, use_llm=False)
        self.assertIn("合同", body)


if __name__ == "__main__":
    unittest.main()
