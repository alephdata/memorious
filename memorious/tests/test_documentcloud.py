from memorious.operations.documentcloud import documentcloud_query


class TestDocumentCloud(object):
    def test_query(self, context, mocker):
        data = {}
        context.params["query"] = "money"

        mocker.patch.object(context, "emit")
        mocker.patch.object(context, "recurse")

        documentcloud_query(context, data)
        assert context.emit.call_count >= 10
        assert context.recurse.call_count == 1
        context.recurse.assert_called_once_with(data={'page': 2})
