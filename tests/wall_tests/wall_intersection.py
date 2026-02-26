import pytest
from bulding_compounds.wall import Wall, walls_intersect_properly


class TestWallIntersection:

    def test_walls_dont_intersect(self):
        """Стіни далеко одна від одної."""
        w1 = Wall(0, 0, 10, 0)
        w2 = Wall(0, 5, 10, 5)  # Паралельні
        assert walls_intersect_properly(w1, w2) is True

    def test_walls_touch_at_corner_L_shape(self):
        """Класичний кут: кінець однієї стіни є початком іншої."""
        w1 = Wall(0, 0, 10, 0)
        w2 = Wall(10, 0, 10, 10)
        # Перетин у точці (10, 0), яка є кінцем w1 і початком w2
        assert walls_intersect_properly(w1, w2) is True

    def test_walls_cross_X_shape_bad(self):
        """Х-подібний перетин"""
        w1 = Wall(0, 0, 10, 10)
        w2 = Wall(0, 10, 10, 0)
        # Перетинаються в (5, 5), це не кінцева точка
        assert walls_intersect_properly(w1, w2) is False

    def test_walls_overlap_bad(self):
        """Накладання стін (колінеарність)"""
        w1 = Wall(0, 0, 10, 0)
        w2 = Wall(5, 0, 15, 0)  # Накладаються від 5 до 10
        assert walls_intersect_properly(w1, w2) is False

    def test_walls_overlap_inside_bad(self):
        """Одна стіна повністю всередині іншої."""
        w1 = Wall(0, 0, 10, 0)
        w2 = Wall(2, 0, 8, 0)
        assert walls_intersect_properly(w1, w2) is False

    def test_identical_walls(self):
        """Стіни ідентичні"""
        w1 = Wall(0, 0, 10, 0)
        w2 = Wall(0, 0, 10, 0)
        assert walls_intersect_properly(w1, w2) is True

    def test_walls_touch_start_to_start(self):
        """Стіни виходять з однієї точки (V-форма)."""
        w1 = Wall(0, 0, 5, 5)
        w2 = Wall(0, 0, 5, -5)
        assert walls_intersect_properly(w1, w2) is True
