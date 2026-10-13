package com.aura.repository;

import com.aura.entity.EnergyIntelligence;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface EnergyIntelligenceRepository extends JpaRepository<EnergyIntelligence, Long> {

    // Retrieve latest intelligence for a specific facility and zone
    Optional<EnergyIntelligence> findTopByFacilityIdAndZoneIdOrderByTimestampDesc(String facilityId, String zoneId);

    // Retrieve recent intelligence records for a specific facility and zone
    List<EnergyIntelligence> findByFacilityIdAndZoneIdOrderByTimestampDesc(String facilityId, String zoneId, Pageable pageable);

    // Retrieve latest detected anomalies for a facility
    List<EnergyIntelligence> findByFacilityIdAndAnomalyDetectedTrueOrderByTimestampDesc(String facilityId, Pageable pageable);
}
