def test_turn_on_reply_is_a_sentence(KoSa):
    assert KoSa.chat("turn on the kitchen light").endswith("The kitchen light is on.")
    assert KoSa.devs["kitchen.light"]["on"] is True


def test_word_order_is_flexible(KoSa):
    KoSa.chat("turn on the kitchen light")
    assert "off" in KoSa.chat("turn the kitchen light off")
    assert KoSa.devs["kitchen.light"]["on"] is False


def test_repeating_a_command_is_acknowledged(KoSa):
    assert "already off" in KoSa.chat("turn off the kitchen light")


def test_state_question(KoSa):
    assert KoSa.chat("is the kitchen light on?") == "The kitchen light is off."


def test_unlock_asks_for_confirmation(KoSa):
    assert "Do you want me to unlock" in KoSa.chat("unlock the front door")
    assert KoSa.devs["living_room.front_door"]["locked"] is True
    assert "unlocked" in KoSa.chat("yes")
    assert KoSa.devs["living_room.front_door"]["locked"] is False


def test_unlock_can_be_declined(KoSa):
    KoSa.chat("unlock the front door")
    assert "leave it" in KoSa.chat("no")
    assert KoSa.devs["living_room.front_door"]["locked"] is True


def test_guest_cannot_unlock(KoSa):
    KoSa.role = "guest"
    assert "guests can't" in KoSa.chat("unlock the front door").lower()


def test_good_night_scene(KoSa):
    KoSa.chat("turn on the kitchen light")
    KoSa.chat("unlock the front door")
    KoSa.chat("yes")
    KoSa.chat("good night")
    assert not any(d["on"] for d in KoSa.devs.values())
    assert all(d["locked"] for d in KoSa.devs.values() if d["type"] == "lock")


def test_emergency_locks_every_door(KoSa):
    KoSa.chat("unlock the front door")
    KoSa.chat("yes")
    assert "locked every door" in KoSa.chat("there is an intruder")
    assert KoSa.devs["living_room.front_door"]["locked"] is True


def test_the_word_help_is_not_an_emergency(KoSa):
    assert "locked every door" not in KoSa.chat("can you help me")


def test_who_are_you(KoSa):
    assert "KoSa" in KoSa.chat("who are you")


def test_word_bank_action_word(KoSa):
    KoSa.words.add("action", "illuminate", "turn on")
    assert "is on" in KoSa.chat("illuminate the kitchen light")


def test_word_bank_nickname(KoSa):
    KoSa.words.add("name", "the cave", "study")
    KoSa.chat("turn on the cave lamp")
    assert KoSa.devs["study.lamp"]["on"] is True


def test_word_bank_phrase_runs_several_commands(KoSa):
    KoSa.words.add("phrase", "movie time", "turn on the kitchen light; turn on the bedside light")
    KoSa.chat("movie time")
    assert KoSa.devs["kitchen.light"]["on"] and KoSa.devs["bedroom.bedside"]["on"]


def test_word_bank_sounds_like(KoSa):
    KoSa.words.add("heard", "kitchin", "kitchen")
    KoSa.chat("turn on the kitchin light")
    assert KoSa.devs["kitchen.light"]["on"] is True


def test_builtin_mishearing_fix(KoSa):
    KoSa.chat("dawn on the kitchen light")
    assert KoSa.devs["kitchen.light"]["on"] is True
