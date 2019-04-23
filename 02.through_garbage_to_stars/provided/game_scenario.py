PHRASES = {
    1957: "First Sputnik",
    1961: "Gagarin flew!",
    1969: "Armstrong got on the moon!",
    1971: "First orbital space station Salute-1",
    1981: "Flight of the Shuttle Columbia",
    1998: 'ISS start building',
    2011: 'Messenger launch to Mercury',
    2020: "Take the plasma gun! Shoot the garbage!",
}


# Темп игры и все события привязаны к годам.
# Один год — это 1.5 секунды игрового времени.
# До 1961 года в космосе чисто и пусто, затем появляется мусор.
# Со временем его становится все больше
# и к 2020 году корабль вооружается плазменной пушкой,
# чтобы было чем расчищать дорогу.
# Чем ближе к 2020 году, тем больше мусора на орбите.
# Частотой его появления управляет функция get_garbage_delay_tics.
# Чтобы было совсем антаружно,
# на экране могут появляться надписи — чем примечателен этот год.


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2
