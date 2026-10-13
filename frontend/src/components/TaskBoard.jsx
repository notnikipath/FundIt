import React from "react";

export function TaskBoard({ updates }) {
  if (!updates?.length) {
    return <div className="empty-board">No campaign updates yet.</div>;
  }

  return (
    <section className="route-lane">
      {updates.map((item) => (
        <article className="route-stop" key={item.update_id}>
          <p className="lesson-type">Update</p>
          <h4>{item.title}</h4>
          <div className="lesson-meta">
            <span>{new Date(item.created_at).toLocaleString()}</span>
            <span>{item.is_voice ? "Voice" : "Text"}</span>
          </div>
        </article>
      ))}
    </section>
  );
}
