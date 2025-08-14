// Script de inicialización para MongoDB
// Este script se ejecuta automáticamente cuando se crea el contenedor

// Cambiar a la base de datos del proyecto
db = db.getSiblingDB('vulnerability_validation');

// Crear colección para reportes de PDFs
db.createCollection('reports');

// Crear índices para mejorar el rendimiento
db.reports.createIndex({ "source_file": 1 });
db.reports.createIndex({ "processed_at": -1 });
db.reports.createIndex({ "created_at": -1 });
db.reports.createIndex({ "title": "text", "content": "text", "summary": "text" });

// Crear índices para búsquedas específicas
db.reports.createIndex({ "metadata.source_file": 1 });
db.reports.createIndex({ "structured_data.documento.titulo": 1 });
db.reports.createIndex({ "structured_data.documento.tipo": 1 });

// Insertar documento de ejemplo para verificar la configuración
db.reports.insertOne({
    title: "Sistema Inicializado",
    content: "Base de datos MongoDB configurada correctamente para PDF Processor",
    summary: "Inicialización exitosa del sistema",
    structured_data: {
        documento: {
            titulo: "Inicialización del Sistema",
            tipo: "system_init"
        }
    },
    metadata: {
        processed_at: new Date().toISOString(),
        source_file: "system_init",
        init_script: "mongo-init/init-db.js"
    },
    processed_at: new Date().toISOString(),
    source_file: "system_init",
    created_at: new Date(),
    updated_at: new Date()
});

print('Base de datos vulnerability_validation inicializada correctamente');
print('Colecciones creadas: reports');
print('Índices creados para optimizar consultas de reportes PDF');