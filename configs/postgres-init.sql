-- PostgreSQL initialization script for oute-mind
-- This script creates the necessary schemas and tables for the estimator system

-- Enable JSON support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schema
CREATE SCHEMA IF NOT EXISTS estimator;

-- Checklists table (Multi-modal discovery)
CREATE TABLE IF NOT EXISTS estimator.checklists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    phase VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Estimation history table (RAG memory)
CREATE TABLE IF NOT EXISTS estimator.estimation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    team_id UUID NOT NULL,
    user_id UUID NOT NULL,
    phase INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Design patterns cache (JSONB for patterns)
CREATE TABLE IF NOT EXISTS estimator.patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    pattern_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Financial scenarios (FinOps results)
CREATE TABLE IF NOT EXISTS estimator.financial_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    estimation_id UUID NOT NULL,
    scenario_type VARCHAR(50) NOT NULL,
    costs JSONB NOT NULL,
    timeline JSONB NOT NULL,
    risks JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_checklists_project_id ON estimator.checklists(project_id);
CREATE INDEX IF NOT EXISTS idx_estimation_history_project_id ON estimator.estimation_history(project_id);
CREATE INDEX IF NOT EXISTS idx_estimation_history_team_id ON estimator.estimation_history(team_id);
CREATE INDEX IF NOT EXISTS idx_patterns_name ON estimator.patterns(pattern_name);
CREATE INDEX IF NOT EXISTS idx_financial_scenarios_estimation_id ON estimator.financial_scenarios(estimation_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION estimator.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables
CREATE TRIGGER update_checklists_timestamp BEFORE UPDATE ON estimator.checklists
    FOR EACH ROW EXECUTE FUNCTION estimator.update_timestamp();

CREATE TRIGGER update_estimation_history_timestamp BEFORE UPDATE ON estimator.estimation_history
    FOR EACH ROW EXECUTE FUNCTION estimator.update_timestamp();

CREATE TRIGGER update_patterns_timestamp BEFORE UPDATE ON estimator.patterns
    FOR EACH ROW EXECUTE FUNCTION estimator.update_timestamp();

-- Grant permissions to application user
GRANT USAGE ON SCHEMA estimator TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA estimator TO PUBLIC;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA estimator TO PUBLIC;

-- =====================================================
-- oute-main Database and Schema Setup
-- =====================================================

-- Create oute_main database for oute-main services (Dashboard, Auth, Projects)
CREATE DATABASE oute_main;

-- Connect to oute_main database and grant permissions
-- Note: These commands should be run separately after database creation
-- Or use: psql -U app-user oute_main < subsequent_grants.sql

-- Grant privileges on oute_main database to app-user
ALTER DATABASE oute_main OWNER TO "app-user";
GRANT CONNECT ON DATABASE oute_main TO "app-user";
GRANT CREATE ON DATABASE oute_main TO "app-user";
