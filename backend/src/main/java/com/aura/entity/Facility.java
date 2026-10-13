package com.aura.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "facilities")
public class Facility {

    @Id
    @Column(name = "facility_id", length = 32, nullable = false)
    private String facilityId;

    @Column(name = "name", length = 128, nullable = false)
    private String name;

    @Column(name = "facility_type", length = 32, nullable = false)
    private String facilityType;

    @Column(name = "location", length = 255)
    private String location;

    @Column(name = "total_floors")
    private Integer totalFloors;

    @Column(name = "created_at", insertable = false, updatable = false)
    private LocalDateTime createdAt;

    public Facility() {
    }

    public Facility(String facilityId, String name, String facilityType, String location, Integer totalFloors) {
        this.facilityId = facilityId;
        this.name = name;
        this.facilityType = facilityType;
        this.location = location;
        this.totalFloors = totalFloors;
    }

    public String getFacilityId() {
        return facilityId;
    }

    public void setFacilityId(String facilityId) {
        this.facilityId = facilityId;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getFacilityType() {
        return facilityType;
    }

    public void setFacilityType(String facilityType) {
        this.facilityType = facilityType;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public Integer getTotalFloors() {
        return totalFloors;
    }

    public void setTotalFloors(Integer totalFloors) {
        this.totalFloors = totalFloors;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }
}
