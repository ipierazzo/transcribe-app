-- =====================================================
-- SCRIPT DE CRIAÇÃO DO BANCO DE DADOS DA CLÍNICA
-- Sistema de Gestão Médica - medIA
-- PostgreSQL Version
-- =====================================================

-- Criar o schema 'clinica'
CREATE SCHEMA IF NOT EXISTS clinica;

-- =====================================================
-- TABELA: PACIENTES
-- =====================================================
CREATE TABLE IF NOT EXISTS clinica.pacientes (
    id_paciente SERIAL PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    data_nascimento DATE NOT NULL,
    sexo VARCHAR(10) CHECK (sexo IN ('M', 'F', 'Outro')) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_pacientes_cpf ON clinica.pacientes(cpf);
CREATE INDEX IF NOT EXISTS idx_pacientes_nome ON clinica.pacientes(nome_completo);
CREATE INDEX IF NOT EXISTS idx_pacientes_data_nascimento ON clinica.pacientes(data_nascimento);

-- =====================================================
-- TABELA: CONSULTAS
-- =====================================================
CREATE TABLE IF NOT EXISTS clinica.consultas (
    id_consulta SERIAL PRIMARY KEY,
    id_paciente INTEGER NOT NULL,
    data_consulta TIMESTAMP NOT NULL,
    motivo_consulta TEXT NOT NULL,
    resultado TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Chave estrangeira para pacientes
    FOREIGN KEY (id_paciente) REFERENCES clinica.pacientes(id_paciente) ON DELETE CASCADE
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_consultas_paciente ON clinica.consultas(id_paciente);
CREATE INDEX IF NOT EXISTS idx_consultas_data ON clinica.consultas(data_consulta);
CREATE INDEX IF NOT EXISTS idx_consultas_motivo ON clinica.consultas(motivo_consulta);

-- =====================================================
-- FUNCTIONS PARA AUDITORIA
-- =====================================================

-- Function para atualizar data_atualizacao na tabela pacientes
CREATE OR REPLACE FUNCTION clinica.update_pacientes_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function para atualizar data_atualizacao na tabela consultas
CREATE OR REPLACE FUNCTION clinica.update_consultas_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.data_atualizacao = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- TRIGGERS PARA AUDITORIA
-- =====================================================

-- Trigger para atualizar data_atualizacao na tabela pacientes
CREATE TRIGGER tr_pacientes_update 
    BEFORE UPDATE ON clinica.pacientes 
    FOR EACH ROW 
    EXECUTE FUNCTION clinica.update_pacientes_timestamp();

-- Trigger para atualizar data_atualizacao na tabela consultas
CREATE TRIGGER tr_consultas_update 
    BEFORE UPDATE ON clinica.consultas 
    FOR EACH ROW 
    EXECUTE FUNCTION clinica.update_consultas_timestamp();

-- =====================================================
-- VIEWS ÚTEIS
-- =====================================================

-- View para consultas com dados do paciente
CREATE OR REPLACE VIEW clinica.vw_consultas_completas AS
SELECT 
    c.id_consulta,
    c.id_paciente,
    p.nome_completo,
    p.cpf,
    p.data_nascimento,
    p.sexo,
    c.data_consulta,
    c.motivo_consulta,
    c.resultado,
    c.data_cadastro,
    c.data_atualizacao
FROM clinica.consultas c
INNER JOIN clinica.pacientes p ON c.id_paciente = p.id_paciente
ORDER BY c.data_consulta DESC;

-- View para estatísticas dos pacientes
CREATE OR REPLACE VIEW clinica.vw_estatisticas_pacientes AS
SELECT 
    COUNT(*) as total_pacientes,
    COUNT(CASE WHEN sexo = 'M' THEN 1 END) as pacientes_masculino,
    COUNT(CASE WHEN sexo = 'F' THEN 1 END) as pacientes_feminino,
    COUNT(CASE WHEN sexo = 'Outro' THEN 1 END) as pacientes_outro,
    AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, data_nascimento))) as idade_media
FROM clinica.pacientes;

-- =====================================================
-- DADOS DE EXEMPLO
-- =====================================================

-- Inserir alguns pacientes de exemplo
INSERT INTO clinica.pacientes (nome_completo, data_nascimento, sexo, cpf) VALUES
('João Silva Santos', '1985-03-15', 'M', '123.456.789-01'),
('Maria Oliveira Costa', '1990-07-22', 'F', '987.654.321-02'),
('Pedro Almeida Souza', '1978-11-08', 'M', '456.789.123-03'),
('Ana Paula Ferreira', '1992-05-30', 'F', '321.654.987-04'),
('Carlos Eduardo Lima', '1983-09-12', 'M', '654.321.789-05');

-- Inserir algumas consultas de exemplo
INSERT INTO clinica.consultas (id_paciente, data_consulta, motivo_consulta, resultado) VALUES
(1, '2024-01-15 09:00:00', 'Consulta de rotina', 'Paciente em bom estado geral. Pressão arterial normal. Recomendado retorno em 6 meses.'),
(1, '2024-02-20 14:30:00', 'Dor de cabeça persistente', 'Realizado exame neurológico. Prescrito analgésico. Retorno em 1 mês se persistir.'),
(2, '2024-01-18 10:15:00', 'Check-up anual', 'Exames laboratoriais normais. Peso e altura adequados. Paciente saudável.'),
(3, '2024-02-10 16:00:00', 'Dor no peito', 'Realizado ECG. Sem alterações. Recomendado acompanhamento cardiológico.'),
(4, '2024-01-25 11:30:00', 'Consulta pré-natal', 'Gestação de 20 semanas. Ultrassom normal. Próxima consulta em 1 mês.');

-- =====================================================
-- FUNCTIONS ÚTEIS
-- =====================================================

-- Function para buscar paciente por CPF
CREATE OR REPLACE FUNCTION clinica.buscar_paciente_por_cpf(p_cpf VARCHAR(14))
RETURNS TABLE(
    id_paciente INTEGER,
    nome_completo VARCHAR(255),
    data_nascimento DATE,
    sexo VARCHAR(10),
    cpf VARCHAR(14),
    data_cadastro TIMESTAMP,
    data_atualizacao TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM clinica.pacientes WHERE cpf = p_cpf;
END;
$$ LANGUAGE plpgsql;

-- Function para listar consultas de um paciente
CREATE OR REPLACE FUNCTION clinica.consultas_por_paciente(p_id_paciente INTEGER)
RETURNS TABLE(
    id_consulta INTEGER,
    data_consulta TIMESTAMP,
    motivo_consulta TEXT,
    resultado TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id_consulta,
        c.data_consulta,
        c.motivo_consulta,
        c.resultado
    FROM clinica.consultas c
    WHERE c.id_paciente = p_id_paciente
    ORDER BY c.data_consulta DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMENTÁRIOS E DOCUMENTAÇÃO
-- =====================================================

-- Comentários nas tabelas
COMMENT ON TABLE clinica.pacientes IS 'Tabela de pacientes da clínica';
COMMENT ON TABLE clinica.consultas IS 'Tabela de consultas médicas';

-- Comentários nas colunas principais
COMMENT ON COLUMN clinica.pacientes.id_paciente IS 'Identificador único do paciente';
COMMENT ON COLUMN clinica.pacientes.nome_completo IS 'Nome completo do paciente';
COMMENT ON COLUMN clinica.pacientes.data_nascimento IS 'Data de nascimento do paciente';
COMMENT ON COLUMN clinica.pacientes.sexo IS 'Sexo do paciente: M=Masculino, F=Feminino, Outro=Outro';
COMMENT ON COLUMN clinica.pacientes.cpf IS 'CPF do paciente (formato: 000.000.000-00)';

COMMENT ON COLUMN clinica.consultas.id_consulta IS 'Identificador único da consulta';
COMMENT ON COLUMN clinica.consultas.id_paciente IS 'ID do paciente (FK)';
COMMENT ON COLUMN clinica.consultas.data_consulta IS 'Data e hora da consulta';
COMMENT ON COLUMN clinica.consultas.motivo_consulta IS 'Motivo da consulta';
COMMENT ON COLUMN clinica.consultas.resultado IS 'Resultado da consulta (texto livre)';

-- =====================================================
-- SCRIPT FINALIZADO
-- =====================================================

SELECT 'Schema clinica criado com sucesso!' as Status;
SELECT 'Tabelas pacientes e consultas criadas!' as Status;
SELECT 'Views, functions e triggers configurados!' as Status;
SELECT 'Dados de exemplo inseridos!' as Status;


