db = db.getSiblingDB("perpustakaan_digital");

db.createCollection("activity_logs", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["timestamp", "action", "username", "role"],
      properties: {
        timestamp: {
          bsonType: "string",
          description: "Waktu pencatatan format ISO 8601"
        },
        action: {
          bsonType: "string",
          description: "Nama aksi aktivitas"
        },
        username: {
          bsonType: "string",
          description: "Username pelaku aksi"
        },
        role: {
          bsonType: "string",
          enum: ["admin", "member", "guest", "system", "unknown"],
          description: "Peran pengguna saat aksi dilakukan"
        },
        user_id: {
          bsonType: ["int", "long", "null"],
          description: "ID pengguna di basis data postgresql"
        },
        ip_address: {
          bsonType: "string",
          description: "Alamat IP klien"
        },
        details: {
          bsonType: "object",
          description: "Objek fleksibel berisi detail metadata"
        }
      }
    }
  }
});

db.activity_logs.createIndex({ "timestamp": -1 });
db.activity_logs.createIndex({ "username": 1 });
db.activity_logs.createIndex({ "action": 1 });
db.activity_logs.createIndex({ "role": 1 });

db.activity_logs.insertMany([
  {
    "timestamp": new Date().toISOString(),
    "action": "SYSTEM_INIT",
    "username": "system",
    "role": "system",
    "user_id": null,
    "ip_address": "127.0.0.1",
    "details": {
      "message": "Inisialisasi koleksi log sistem perpustakaan digital"
    }
  },
  {
    "timestamp": new Date().toISOString(),
    "action": "LOGIN_SUCCESS",
    "username": "admin",
    "role": "admin",
    "user_id": 1,
    "ip_address": "127.0.0.1",
    "details": {
      "user_agent": "Mozilla/5.0"
    }
  }
]);
