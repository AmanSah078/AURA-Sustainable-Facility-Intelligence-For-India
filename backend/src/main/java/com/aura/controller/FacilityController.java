package com.aura.controller;

import com.aura.entity.Facility;
import com.aura.service.EnergyService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/facilities")
@CrossOrigin(origins = "*")
public class FacilityController {

    private final EnergyService energyService;

    public FacilityController(EnergyService energyService) {
        this.energyService = energyService;
    }

    /**
     * Retrieve all configured facilities.
     * GET /api/v1/facilities
     */
    @GetMapping
    public ResponseEntity<List<Facility>> getAllFacilities() {
        return ResponseEntity.ok(energyService.getAllFacilities());
    }

    /**
     * Retrieve facility metadata by ID (e.g. H001).
     * GET /api/v1/facilities/{facilityId}
     */
    @GetMapping("/{facilityId}")
    public ResponseEntity<Facility> getFacilityById(@PathVariable String facilityId) {
        return energyService.getFacility(facilityId)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
