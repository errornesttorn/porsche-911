package sim

import (
	"encoding/json"
	"os"
	"runtime"
	"testing"
)

func TestBrakingC(t *testing.T) {
	data, err := os.ReadFile("../testdata/crash_state.json")
	if err != nil {
		// Try to create a minimal test with synthetic data
		t.Log("No crash_state.json found, using synthetic test")
		testBrakingCSynthetic(t)
		return
	}
	var w World
	if err := json.Unmarshal(data, &w); err != nil {
		t.Fatal(err)
	}
	t.Logf("Loaded world with %d cars, %d splines", len(w.Cars), len(w.Splines))
	w.RebuildAllSplines()
	vehicleCounts := BuildVehicleCounts(w.Cars)
	graph := NewRoadGraph(w.Splines, vehicleCounts)
	flags, hold, _, _, _, prof := computeBrakingDecisionsC(w.Cars, graph, -1, 0)
	t.Logf("Profile: %+v", prof)
	t.Logf("Braking: %d, Hold: %d", countTrue(flags), countTrue(hold))
}

func TestWorldStepCStress(t *testing.T) {
	world, err := LoadWorld("../tests/pathfinding_highway_test.json")
	if err != nil {
		t.Fatal(err)
	}
	for i := range world.Routes {
		world.Routes[i].SpawnPerMinute *= 5
	}

	maxCars := len(world.Cars)
	for step := 0; step < 800; step++ {
		world.Step(1.0 / 30.0)
		if len(world.Cars) > maxCars {
			maxCars = len(world.Cars)
		}
		if step%50 == 49 {
			runtime.GC()
		}
	}
	t.Logf("stress run complete: cars=%d maxCars=%d brakingMS=%.3f", len(world.Cars), maxCars, world.BrakingMS)
}

func testBrakingCSynthetic(t *testing.T) {
	// Create two splines forming a simple road
	sp1 := Spline{
		ID:          1,
		P0:          Vec2{0, 0},
		P1:          Vec2{10, 0},
		P2:          Vec2{20, 0},
		P3:          Vec2{30, 0},
		Length:       30,
		SpeedFactor: 1.0,
	}
	sp2 := Spline{
		ID:          2,
		P0:          Vec2{30, 0},
		P1:          Vec2{40, 0},
		P2:          Vec2{50, 0},
		P3:          Vec2{60, 0},
		Length:       30,
		SpeedFactor: 1.0,
	}
	splines := []Spline{sp1, sp2}
	for i := range splines {
		RebuildSpline(&splines[i])
	}

	cars := []Car{
		{
			ID: 1, RouteID: 1,
			CurrentSplineID: 1, DestinationSplineID: 2,
			DistanceOnSpline: 5, Speed: 10, MaxSpeed: 15, Accel: 3,
			Length: 4, Width: 2,
			RearPosition:  Vec2{3, 0},
			PrevSplineIDs: [2]int{-1, -1},
			LaneChangeSplineID: -1, AfterSplineID: -1, DesiredLaneSplineID: -1,
		},
		{
			ID: 2, RouteID: 2,
			CurrentSplineID: 1, DestinationSplineID: 2,
			DistanceOnSpline: 15, Speed: 5, MaxSpeed: 15, Accel: 3,
			Length: 4, Width: 2,
			RearPosition:  Vec2{13, 0},
			PrevSplineIDs: [2]int{-1, -1},
			LaneChangeSplineID: -1, AfterSplineID: -1, DesiredLaneSplineID: -1,
		},
		{
			ID: 3, RouteID: 3,
			CurrentSplineID: 2, DestinationSplineID: 2,
			DistanceOnSpline: 10, Speed: 8, MaxSpeed: 15, Accel: 3,
			Length: 4, Width: 2,
			RearPosition:  Vec2{38, 0},
			PrevSplineIDs: [2]int{-1, -1},
			LaneChangeSplineID: -1, AfterSplineID: -1, DesiredLaneSplineID: -1,
		},
	}

	vehicleCounts := BuildVehicleCounts(cars)
	graph := NewRoadGraph(splines, vehicleCounts)
	t.Logf("Graph: %d splines", len(graph.splines))

	flags, hold, _, _, _, prof := computeBrakingDecisionsC(cars, graph, -1, 0)
	t.Logf("Profile: %+v", prof)
	t.Logf("Braking: %d, Hold: %d", countTrue(flags), countTrue(hold))
}

func countTrue(b []bool) int {
	n := 0
	for _, v := range b {
		if v {
			n++
		}
	}
	return n
}
