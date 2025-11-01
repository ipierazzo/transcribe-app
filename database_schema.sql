-- =====================================================
-- SCRIPT DE CRIAÇÃO DO BANCO DE DADOS DA CLÍNICA
-- Sistema de Gestão Médica - medIA
-- =====================================================

-- Criar o schema 'clinica'
CREATE SCHEMA IF NOT EXISTS clinica;

-- Usar o schema clinica
USE clinica;

-- =====================================================
-- TABELA: PACIENTES
-- =====================================================
CREATE TABLE IF NOT EXISTS clinica.pacientes (
    id_paciente INT AUTO_INCREMENT PRIMARY KEY,
    nome_completo VARCHAR(255) NOT NULL,
    data_nascimento DATE NOT NULL,
    sexo ENUM('M', 'F', 'Outro') NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices para melhor performance
    INDEX idx_cpf (cpf),
    INDEX idx_nome (nome_completo),
    INDEX idx_data_nascimento (data_nascimento)
);

-- =====================================================
-- TABELA: CONSULTAS
-- =====================================================
CREATE TABLE IF NOT EXISTS clinica.consultas (
    id_consulta INT AUTO_INCREMENT PRIMARY KEY,
    id_paciente INT NOT NULL,
    data_consulta DATETIME NOT NULL,
    motivo_consulta TEXT NOT NULL,
    resultado TEXT,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Chave estrangeira para pacientes
    FOREIGN KEY (id_paciente) REFERENCES clinica.pacientes(id_paciente) ON DELETE CASCADE,
    
    -- Índices para melhor performance
    INDEX idx_paciente (id_paciente),
    INDEX idx_data_consulta (data_consulta),
    INDEX idx_motivo (motivo_consulta(100))
);

-- =====================================================
-- TRIGGERS PARA AUDITORIA
-- =====================================================

-- Trigger para atualizar data_atualizacao na tabela pacientes
DELIMITER $$
CREATE TRIGGER tr_pacientes_update 
    BEFORE UPDATE ON clinica.pacientes 
    FOR EACH ROW 
BEGIN
    SET NEW.data_atualizacao = CURRENT_TIMESTAMP;
END$$
DELIMITER ;

-- Trigger para atualizar data_atualizacao na tabela consultas
DELIMITER $$
CREATE TRIGGER tr_consultas_update 
    BEFORE UPDATE ON clinica.consultas 
    FOR EACH ROW 
BEGIN
    SET NEW.data_atualizacao = CURRENT_TIMESTAMP;
END$$
DELIMITER ;

-- =====================================================
-- VIEWS ÚTEIS
-- =====================================================

-- View para consultas com dados do paciente
CREATE VIEW clinica.vw_consultas_completas AS
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
CREATE VIEW clinica.vw_estatisticas_pacientes AS
SELECT 
    COUNT(*) as total_pacientes,
    COUNT(CASE WHEN sexo = 'M' THEN 1 END) as pacientes_masculino,
    COUNT(CASE WHEN sexo = 'F' THEN 1 END) as pacientes_feminino,
    COUNT(CASE WHEN sexo = 'Outro' THEN 1 END) as pacientes_outro,
    AVG(YEAR(CURDATE()) - YEAR(data_nascimento)) as idade_media
FROM clinica.pacientes;

-- =====================================================
-- DADOS DE EXEMPLO (OPCIONAL)
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
-- PROCEDURES ÚTEIS
-- =====================================================

-- Procedure para buscar paciente por CPF
DELIMITER $$
CREATE PROCEDURE clinica.sp_buscar_paciente_por_cpf(IN p_cpf VARCHAR(14))
BEGIN
    SELECT * FROM clinica.pacientes WHERE cpf = p_cpf;
END$$
DELIMITER ;

-- Procedure para listar consultas de um paciente
DELIMITER $$
CREATE PROCEDURE clinica.sp_consultas_por_paciente(IN p_id_paciente INT)
BEGIN
    SELECT 
        c.id_consulta,
        c.data_consulta,
        c.motivo_consulta,
        c.resultado
    FROM clinica.consultas c
    WHERE c.id_paciente = p_id_paciente
    ORDER BY c.data_consulta DESC;
END$$
DELIMITER ;

-- =====================================================
-- COMENTÁRIOS E DOCUMENTAÇÃO
-- =====================================================

-- Comentários nas tabelas
ALTER TABLE clinica.pacientes COMMENT = 'Tabela de pacientes da clínica';
ALTER TABLE clinica.consultas COMMENT = 'Tabela de consultas médicas';

-- Comentários nas colunas principais
ALTER TABLE clinica.pacientes MODIFY COLUMN id_paciente INT AUTO_INCREMENT COMMENT 'Identificador único do paciente';
ALTER TABLE clinica.pacientes MODIFY COLUMN nome_completo VARCHAR(255) NOT NULL COMMENT 'Nome completo do paciente';
ALTER TABLE clinica.pacientes MODIFY COLUMN data_nascimento DATE NOT NULL COMMENT 'Data de nascimento do paciente';
ALTER TABLE clinica.pacientes MODIFY COLUMN sexo ENUM('M', 'F', 'Outro') NOT NULL COMMENT 'Sexo do paciente: M=Masculino, F=Feminino, Outro=Outro';
ALTER TABLE clinica.pacientes MODIFY COLUMN cpf VARCHAR(14) UNIQUE NOT NULL COMMENT 'CPF do paciente (formato: 000.000.000-00)';

ALTER TABLE clinica.consultas MODIFY COLUMN id_consulta INT AUTO_INCREMENT COMMENT 'Identificador único da consulta';
ALTER TABLE clinica.consultas MODIFY COLUMN id_paciente INT NOT NULL COMMENT 'ID do paciente (FK)';
ALTER TABLE clinica.consultas MODIFY COLUMN data_consulta DATETIME NOT NULL COMMENT 'Data e hora da consulta';
ALTER TABLE clinica.consultas MODIFY COLUMN motivo_consulta TEXT NOT NULL COMMENT 'Motivo da consulta';
ALTER TABLE clinica.consultas MODIFY COLUMN resultado TEXT COMMENT 'Resultado da consulta (texto livre)';

-- =====================================================
-- SCRIPT FINALIZADO
-- =====================================================

SELECT 'Schema clinica criado com sucesso!' as Status;
SELECT 'Tabelas pacientes e consultas criadas!' as Status;
SELECT 'Views, procedures e triggers configurados!' as Status;
SELECT 'Dados de exemplo inseridos!' as Status;


