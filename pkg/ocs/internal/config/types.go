package config

// MetricSemanticsConfig represents semantic config for a metric
type MetricSemanticsConfig struct {
	DescriptiveName string `yaml:"descriptive_name"`
	Unit            string `yaml:"unit"`
	Type            string `yaml:"type"`
	Description     string `yaml:"description"`
}

// MetricTemporalConfig represents temporal config for a metric
type MetricTemporalConfig struct {
	GranularityResolution string `yaml:"granularity_resolution"`
	RetentionPolicy       string `yaml:"retention_policy"`
}

// MetricConstraintsConfig represents constraints config for a metric
type MetricConstraintsConfig struct {
	Thresholds map[string]float64 `yaml:"thresholds"`
	Polarity   string             `yaml:"polarity"`
	Aggregator string             `yaml:"aggregator"`
}

// MetricConfigV2 represents a metric configuration block
type MetricConfigV2 struct {
	Name        string                  `yaml:"name"`
	Semantics   MetricSemanticsConfig   `yaml:"semantics"`
	Temporal    MetricTemporalConfig    `yaml:"temporal"`
	Constraints MetricConstraintsConfig `yaml:"constraints"`
}

// IdentityAndOriginConfig represents structural identity mappings
type IdentityAndOriginConfig struct {
	ProviderSource  string `yaml:"provider_source"`
	Environment     string `yaml:"environment"`
	NamespaceDomain string `yaml:"namespace_domain"`
}

// TopologyConfig represents structural topology mapping config
type TopologyConfig struct {
	ResourceType     string                 `yaml:"resource_type"`
	ParentChildLinks map[string]interface{} `yaml:"parent_child_links"`
	LabelsTags       map[string]string      `yaml:"labels_tags"`
}

// OCSConfig represents the OCS configuration structure loaded from ocs_config_v2.yaml
type OCSConfig struct {
	IdentityAndOrigin        IdentityAndOriginConfig `yaml:"identity_and_origin"`
	DimensionalityAndTopology TopologyConfig          `yaml:"dimensionality_and_topology"`
	Metrics                  []MetricConfigV2        `yaml:"metrics"`
	Workload                 []string                `yaml:"workload"`
	TimeWindowMinutes        *int                    `yaml:"time_window_minutes"`
	Policy                   []string                `yaml:"policy"`
}

// PrometheusConfig represents Prometheus configuration
type PrometheusConfig struct {
	PrometheusInstances []struct {
		Name       string            `yaml:"name"`
		BaseURL    string            `yaml:"base_url"`
		Headers    map[string]string `yaml:"headers"`
		DisableSSL bool              `yaml:"disable_ssl"`
	} `yaml:"prometheus_instances"`
}

// IdentityAndOrigin represents the OCS Identity & Origin dimension
type IdentityAndOrigin struct {
	Who   map[string]interface{} `json:"who"`
	Where map[string]interface{} `json:"where"`
}

// DimensionalityAndTopology represents the OCS Dimensionality & Topology dimension
type DimensionalityAndTopology struct {
	NodeType      string                 `json:"node_type"`
	Relationships map[string]interface{} `json:"relationships"`
}

// MetricSemanticInfo represents the OCS Metric Semantics dimension
type MetricSemanticInfo struct {
	Name        string                 `json:"name"`
	Type        string                 `json:"type"`
	Unit        string                 `json:"unit"`
	Description string                 `json:"description"`
	Semantics   map[string]interface{} `json:"semantics,omitempty"`
}

// TemporalBehaviorInfo represents temporal logic/aggregations for a specific metric
type TemporalBehaviorInfo struct {
	Mode                string `json:"mode"`
	AggregationDuration string `json:"aggregation_duration,omitempty"`
	Description         string `json:"description,omitempty"`
}

// TemporalContext represents the OCS Temporal Context dimension
type TemporalContext struct {
	Timestamp         string                          `json:"timestamp,omitempty"`
	TimeWindowMinutes int                             `json:"time_window_minutes"`
	SampleInterval    string                          `json:"sample_interval,omitempty"`
	TemporalBehavior  map[string]TemporalBehaviorInfo `json:"temporal_behavior,omitempty"`
}

// HealthConfigConstraint represents health thresholds/interpretation rules
type HealthConfigConstraint struct {
	MetricName        string                 `json:"metric_name"`
	AggregationLogic  string                 `json:"aggregation_logic,omitempty"`
	WarningThreshold  float64                `json:"warning_threshold,omitempty"`
	CriticalThreshold float64                `json:"critical_threshold,omitempty"`
	Polarity          string                 `json:"polarity,omitempty"`
	ContextCriteria   map[string]interface{} `json:"context_criteria,omitempty"`
	Description       string                 `json:"description,omitempty"`
}

// OperationalConstraints represents the OCS Operational Constraints dimension
type OperationalConstraints struct {
	HealthConfig []HealthConfigConstraint `json:"health_config,omitempty"`
	Policies     []string                 `json:"policies,omitempty"`
}

// ProvenanceEntry captures the lineage of a context fact
type ProvenanceEntry struct {
	Value      interface{} `json:"value,omitempty"`
	Provenance string      `json:"provenance"` // observed, derived, configured, policy, unknown
	Source     interface{} `json:"source,omitempty"`     // e.g. string or []string
}

// OCSContextDefinition represents a context definition in the OCS prompt response
type OCSContextDefinition struct {
	ResourceID                string                    `json:"resource_id"`
	Domain                    string                    `json:"domain"`
	IdentityAndOrigin         IdentityAndOrigin         `json:"identity_and_origin"`
	DimensionalityAndTopology DimensionalityAndTopology `json:"dimensionality_and_topology"`
	MetricSemantics           []MetricSemanticInfo      `json:"metric_semantics"`
	TemporalContext           TemporalContext           `json:"temporal_context"`
	OperationalConstraints    OperationalConstraints    `json:"operational_constraints"`
	ProvenanceMap             map[string]ProvenanceEntry `json:"provenance_map,omitempty"`
}

// OCSPromptResponse represents the OCS prompt response structure
type OCSPromptResponse struct {
	SpecVersion        string                 `json:"spec_version"`
	ContextDefinitions []OCSContextDefinition `json:"context_definitions"`
}

