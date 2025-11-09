"use client";

import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
  TextField,
  MenuItem,
  Slider,
  FormControl,
  InputLabel,
  Select,
} from "@mui/material";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  ResponsiveContainer,
} from "recharts";

const API_BASE =
  "https://diet-processor-func-dnfzf2bvcpbrf4by.westus2-01.azurewebsites.net/api/diet-processor";

// Color palette for charts
const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff8042'];

export default function Dashboard() {
  const [macronutrients, setMacronutrients] = useState<any>({});
  const [cuisineDistribution, setCuisineDistribution] = useState<any>({});
  const [comparisonData, setComparisonData] = useState<any[]>([]);
  const [topRecipes, setTopRecipes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [isClient, setIsClient] = useState(false);

  // Dynamic parameters for top-recipes API
  const [selectedNutrient, setSelectedNutrient] = useState("Protein");
  const [recipeCount, setRecipeCount] = useState(10);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Fetch functions
  const getMacronutrients = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/macronutrients`);
      const data = await res.json();
      setMacronutrients(data);
    } catch (error) {
      console.error('Error fetching macronutrients:', error);
    }
    setLoading(false);
  };

  const getCuisineDistribution = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/cuisine-distribution`);
      const data = await res.json();
      setCuisineDistribution(data);
    } catch (error) {
      console.error('Error fetching cuisine distribution:', error);
    }
    setLoading(false);
  };

  const getComparison = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/comparison`);
      const data = await res.json();
      setComparisonData(data);
    } catch (error) {
      console.error('Error fetching comparison data:', error);
    }
    setLoading(false);
  };

  const getTopRecipes = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/top-recipes?nutrient=${selectedNutrient}&n=${recipeCount}`);
      const data = await res.json();
      setTopRecipes(data);
    } catch (error) {
      console.error('Error fetching top recipes:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    if (isClient) {
      getMacronutrients();
      getCuisineDistribution();
      getComparison();
      getTopRecipes();
    }
  }, [isClient]);

  // Update top recipes when parameters change
  useEffect(() => {
    if (isClient) {
      getTopRecipes();
    }
  }, [selectedNutrient, recipeCount, isClient]);

  // Transform data for charts
  const transformMacronutrientsForChart = () => {
    return Object.entries(macronutrients).map(([dietType, nutrients]: [string, any]) => ({
      dietType,
      protein: nutrients.Protein || 0,
      carbs: nutrients.Carbs || 0,
      fat: nutrients.Fat || 0,
    }));
  };

  const transformCuisineDistributionForChart = () => {
    if (!cuisineDistribution || Object.keys(cuisineDistribution).length === 0) return [];

    const allCuisines: { [key: string]: number } = {};
    Object.values(cuisineDistribution).forEach((dietCuisines: any) => {
      Object.entries(dietCuisines).forEach(([cuisine, count]: [string, any]) => {
        allCuisines[cuisine] = (allCuisines[cuisine] || 0) + count;
      });
    });

    return Object.entries(allCuisines)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 6)
      .map(([cuisine, count]) => ({
        cuisine,
        count,
      }));
  };

  const transformTopRecipesForChart = () => {
    return topRecipes.map((recipe, index) => ({
      rank: index + 1,
      name: recipe.recipe_name,
      value: recipe.nutrient_value,
      dietType: recipe.diet_type,
      cuisine: recipe.cuisine_type,
    }));
  };

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Nutrition Analysis Dashboard
      </Typography>

      <Typography variant="h6" sx={{ mt: 3 }}>
        Data Visualization
      </Typography>

      {/* Dynamic Parameters Control Panel */}
      <Card sx={{ p: 3, mt: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Top Recipes Parameters
        </Typography>
        <Stack direction="row" spacing={3} alignItems="center">
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Nutrient Type</InputLabel>
            <Select
              value={selectedNutrient}
              label="Nutrient Type"
              onChange={(e) => setSelectedNutrient(e.target.value)}
            >
              <MenuItem value="Protein">Protein</MenuItem>
              <MenuItem value="Carbs">Carbohydrates</MenuItem>
              <MenuItem value="Fat">Fat</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ width: 300 }}>
            <Typography gutterBottom>Number of Recipes: {recipeCount}</Typography>
            <Slider
              value={recipeCount}
              onChange={(e, newValue) => setRecipeCount(newValue as number)}
              valueLabelDisplay="auto"
              step={5}
              marks
              min={5}
              max={50}
            />
          </Box>
        </Stack>
      </Card>

      <Stack direction="row" spacing={3} sx={{ mt: 2, flexWrap: "wrap" }}>
        {/* Macronutrient Bar Chart */}
        <Card sx={{ p: 2, width: 350 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            Macronutrient Analysis
          </Typography>
          <Typography variant="body2">Average nutrient content by diet type</Typography>
          <BarChart width={320} height={250} data={transformMacronutrientsForChart()}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="dietType" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="protein" fill="#8884d8" name="Protein(g)" />
            <Bar dataKey="carbs" fill="#82ca9d" name="Carbs(g)" />
            <Bar dataKey="fat" fill="#ffc658" name="Fat(g)" />
          </BarChart>
        </Card>

        {/* Comparison Scatter Plot */}
        <Card sx={{ p: 2, width: 350 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            Nutritional Relationship
          </Typography>
          <Typography variant="body2">
            Protein vs Carbohydrate relationship
          </Typography>
          <ScatterChart width={320} height={250} data={comparisonData}>
            <CartesianGrid />
            <XAxis dataKey="protein" name="Protein" />
            <YAxis dataKey="carbs" name="Carbohydrates" />
            <Tooltip formatter={(value: any, name: any) => [value + 'g', name]} />
            <Scatter dataKey="protein" fill="#2e7d32" />
          </ScatterChart>
        </Card>

        {/* Cuisine Distribution Pie Chart */}
        <Card sx={{ p: 2, width: 350 }}>
          <Typography variant="subtitle1" fontWeight="bold">
            Cuisine Distribution
          </Typography>
          <Typography variant="body2">
            Recipe distribution by cuisine type
          </Typography>
          <PieChart width={320} height={250}>
            <Pie
              data={transformCuisineDistributionForChart()}
              dataKey="count"
              nameKey="cuisine"
              cx="50%"
              cy="50%"
              outerRadius={80}
              fill="#8884d8"
              label
            >
              {transformCuisineDistributionForChart().map((entry, i) => (
                <Cell
                  key={i}
                  fill={COLORS[i % 4]}
                />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </Card>
      </Stack>

      {/* Top Recipes Chart */}
      <Card sx={{ p: 3, mt: 3, width: '100%' }}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Top {recipeCount} Recipes by {selectedNutrient} Content
        </Typography>
        <Typography variant="body2" gutterBottom sx={{ mb: 2 }}>
          Highest {selectedNutrient.toLowerCase()} content recipes from the dataset
        </Typography>
        <Box sx={{ width: '100%', height: 400 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={transformTopRecipesForChart()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="rank"
                label={{ value: 'Recipe Rank', position: 'insideBottom', offset: -5 }}
              />
              <YAxis
                label={{ value: `${selectedNutrient} (g)`, angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                formatter={(value: any) => [`${value}g`, selectedNutrient]}
                labelFormatter={(rank: any) => {
                  const recipe = transformTopRecipesForChart().find(r => r.rank === rank);
                  return recipe ? `#${rank}: ${recipe.name}` : `Recipe #${rank}`;
                }}
              />
              <Bar dataKey="value" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </Card>

      {/* Recipe Details */}
      <Card sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" fontWeight="bold" gutterBottom>
          Top Recipes Details
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 2, mt: 2 }}>
          {topRecipes.slice(0, 6).map((recipe, index) => (
            <Card key={index} sx={{ p: 2, bgcolor: index < 3 ? 'primary.light' : 'grey.100' }}>
              <Typography variant="subtitle2" fontWeight="bold">
                #{index + 1} {recipe.recipe_name}
              </Typography>
              <Typography variant="body2">
                {selectedNutrient}: {recipe.nutrient_value?.toFixed(1)}g
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Diet: {recipe.diet_type} | Cuisine: {recipe.cuisine_type}
              </Typography>
            </Card>
          ))}
        </Box>
      </Card>

      {/* API Buttons */}
      <Box sx={{ mt: 4 }}>
        <Typography variant="h6">Data Controls</Typography>
        <Stack direction="row" spacing={2} sx={{ mt: 1 }}>
          <Button variant="contained" onClick={getMacronutrients} disabled={loading}>
            Get Nutrition Data
          </Button>
          <Button variant="contained" color="success" onClick={getComparison} disabled={loading}>
            Get Comparison Data
          </Button>
          <Button variant="contained" color="secondary" onClick={getCuisineDistribution} disabled={loading}>
            Get Cuisine Distribution
          </Button>
          <Button variant="contained" color="warning" onClick={getTopRecipes} disabled={loading}>
            Refresh Top Recipes
          </Button>
        </Stack>
      </Box>

      <Typography variant="body2" textAlign="center" sx={{ mt: 6, color: "gray" }}>
        © 2025 Nutrition Analysis Dashboard. Azure Functions & Next.js
      </Typography>
    </Box>
  );
}
