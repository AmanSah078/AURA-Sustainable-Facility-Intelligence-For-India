package com.aura.repository;

import com.aura.entity.EnergyReading;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface EnergyReadingRepository extends JpaRepository<EnergyReading, Long> {

    // Retrieve the most recent reading for a specific facility and zone by timestamp
    Optional<EnergyReading> findTopByFacilityIdAndZoneIdOrderByTimestampDesc(String facilityId, String zoneId);

    // Retrieve the most recently ingested reading for a specific facility and zone by ID
    Optional<EnergyReading> findTopByFacilityIdAndZoneIdOrderByIdDesc(String facilityId, String zoneId);

    // Retrieve recent readings for a specific facility and zone by timestamp
    List<EnergyReading> findByFacilityIdAndZoneIdOrderByTimestampDesc(String facilityId, String zoneId, Pageable pageable);

    // Retrieve recent readings for a specific facility and zone by insertion ID (most recently ingested packets)
    List<EnergyReading> findByFacilityIdAndZoneIdOrderByIdDesc(String facilityId, String zoneId, Pageable pageable);

    // Count readings for a specific facility and zone
    long countByFacilityIdAndZoneId(String facilityId, String zoneId);
}
