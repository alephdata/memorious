from memorious.operations.documentcloud import documentcloud_query


class TestDocumentCloud(object):
    def test_query(self, context, mocker):
        data = {}
        context.params["query"] = "money"

        mocker.patch.object(context, "emit")
        mocker.patch.object(context, "recurse")

        documentcloud_query(context, data)
        assert context.emit.call_count == 100
        assert context.recurse.called_once_with(data={'page': 2})
