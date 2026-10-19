def test_add_and_find_book(KoSa):
    assert "Added" in KoSa.chat("add book Dune by Frank Herbert in the Study shelf 2")
    reply = KoSa.chat("where is dune")
    assert "Frank Herbert" in reply and "study" in reply.lower() and "shelf 2" in reply


def test_book_without_room_is_still_saved(KoSa):
    reply = KoSa.chat("add book Emma by Jane Austen")
    assert "which room" in reply
    assert KoSa.lib.search("emma")[0]["author"] == "Jane Austen"


def test_list_and_search_by_author(KoSa):
    KoSa.chat("add book Dune by Frank Herbert")
    KoSa.chat("add book Emma by Jane Austen")
    assert "Emma" in KoSa.chat("list books")
    assert "Jane Austen" in KoSa.chat("books by austen")
