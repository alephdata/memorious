import json
import six
from memorious.logic.context import Context, handle
from memorious.model import Event
from memorious.core import local_queue


class TestContext(object):

    def test_context(self, context):
        assert isinstance(context.run_id, six.string_types)

    def test_content_hash(self, context):
        content_hash = context.store_data(json.dumps({"hello": "world"}))
        assert isinstance(content_hash, six.string_types)
        with context.load_file(content_hash) as fh:
            assert hasattr(fh, "read")

    def test_dump_load_state(self, context, crawler, stage):
        dump = context.dump_state()
        new_context = Context.from_state(dump, stage.name)
        assert isinstance(new_context, Context)
        assert new_context.run_id == context.run_id
        assert new_context.crawler.name == crawler.name
        assert new_context.stage.name == stage.name
        assert all(
            (k, v) in new_context.state.items()
            for k, v in context.state.items()
        )

    def test_emit_exception(self, context):
        exc = Exception("Uh oh!")
        event = context.emit_exception(exc)
        assert isinstance(event, Event)
        assert event.level == Event.LEVEL_ERROR

    def test_emit_warning(self, context):
        msg = "hello"
        event = context.emit_warning(msg)
        assert isinstance(event, Event)
        assert event.level == Event.LEVEL_WARNING

    def test_execute(self, context, mocker):
        data = {"answer": 42}
        mocker.patch("memorious.logic.stage.CrawlerStage.method",
                     new_callable=mocker.PropertyMock)
        context.execute(data)
        assert context.stage.method.call_count == 1
        context.stage.method.assert_called_once_with(context, data)


def test_handle_execute(stage, context, mocker):
    mocker.patch.object(Context, "from_state", return_value=context)
    mocker.patch.object(local_queue, "queue_operation")
    data = {"hello": "world"}
    handle({"foo": "bar"}, stage, data)
    assert local_queue.queue_operation.call_count == 1
    local_queue.queue_operation.assert_called_once_with(context, data)
