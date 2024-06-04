"""
Test for the recipe API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer
)


RECIPE_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """
    Return recipe detail URL
    """
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_recipe(user, **params):
    """
    Create and return a sample recipe
    """
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': Decimal('5.00'),
        'description': 'Sample description',
        'link': 'https://sample.com/sample-recipe'
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def create_user(**params):
    """
    Create and return a sample user
    """
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """
    Test unauthenticated recipe API access
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test that authentication is required
        """
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """
    Test authenticated recipe API access
    """

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='testpass')

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """
        Test retrieving a list of recipes
        """
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """
        Test retrieving recipes for user
        """
        user2 = create_user(
            email="test_user@example.com",
            password="testpass"
        )

        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """
        Test viewing a recipe detail
        """
        recipe = sample_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """
        Test creating recipe
        """
        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 30,
            'price': Decimal('5.00')
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_partial_update_recipe(self):
        """
        Test updating a recipe with patch
        """
        original_link = 'https://sample.com/recipe.pdf'
        recipe = sample_recipe(
            user=self.user,
            title='Sample Recipe title',
            link=original_link
        )

        payload = {'title': 'New title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        """
        Test full update of recipe
        """
        recipe = sample_recipe(
            user=self.user,
            title="Sample title",
            link="https://example.com/recipe.pdf",
            description='Sample Desc'
        )

        payload = {
            'title': 'Curry of life',
            'link': 'https://example.com/naruto.grandma',
            'description': 'Lee\'s favorite',
            'time_minutes': 30,
            'price': Decimal('32.25')
        }

        url = detail_url(recipe_id=recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()

        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_update_user(self):
        """
        Test that updating the user field returns an error
        """
        user2 = create_user(
            email="test2@example.com",
            password="testpass",
        )
        recipe = sample_recipe(user=self.user)

        payload = {
            'user': user2
        }
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """
        Test deleting a recipe
        """
        recipe = sample_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Recipe.objects.filter(id=recipe.id).count(), 0)

    def test_delete_other_users_recipe_error(self):
        """
        Test that a user cannot access another user's recipe
        """
        user2 = create_user(
            email="test@example.com",
            password="testpass"
        )
        recipe = sample_recipe(user=user2)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Recipe.objects.filter(id=recipe.id).count(), 1)
